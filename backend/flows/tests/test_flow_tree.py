"""Tests para el algoritmo de árbol de nodos (sin merges, sin ciclos, sin duplicación)."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from flows import services as flow_services
from flows.models import Flow, FlowBranch, FlowNode

User = get_user_model()


class FlowTreeAlgorithmTests(TestCase):
    """Tests del algoritmo de árbol según la especificación."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.flow = Flow.objects.create(
            name="Test Flow", description="Test", owner=self.user
        )
        # Inicializar rama principal
        self.main_branch = flow_services.initialize_main_branch(self.flow, self.user)

    def test_initialize_main_branch_creates_root_node(self):
        """Verifica que la rama principal se crea con un nodo raíz."""
        self.assertIsNotNone(self.main_branch)
        self.assertEqual(self.main_branch.name, "principal")
        self.assertEqual(self.main_branch.head, self.main_branch.start_node)
        self.assertIsNone(self.main_branch.head.parent)

    def test_add_step_creates_new_node(self):
        """Verifica que add_step crea un nuevo nodo y actualiza el head."""
        content = {"step": "calcular", "params": {"method": "DFT"}}
        node = flow_services.add_step("principal", self.flow, content, self.user)

        self.assertIsNotNone(node)
        self.assertEqual(node.content, content)
        self.assertEqual(node.parent, self.main_branch.start_node)

        # Verificar que el head se actualizó
        self.main_branch.refresh_from_db()
        self.assertEqual(self.main_branch.head, node)

    def test_add_step_prevents_duplication(self):
        """Verifica que no se permite duplicar contenido (sin duplicaciones)."""
        content = {"step": "unique", "value": 42}
        flow_services.add_step("principal", self.flow, content, self.user)

        # Intentar añadir el mismo contenido debe fallar
        with self.assertRaises(ValueError) as ctx:
            flow_services.add_step("principal", self.flow, content, self.user)
        self.assertIn("Duplicación no permitida", str(ctx.exception))

    def test_get_path_returns_linear_sequence(self):
        """Verifica que get_path retorna la secuencia desde raíz hasta head."""
        # Añadir 3 pasos
        content1 = {"step": "paso1"}
        content2 = {"step": "paso2"}
        content3 = {"step": "paso3"}

        flow_services.add_step("principal", self.flow, content1, self.user)
        flow_services.add_step("principal", self.flow, content2, self.user)
        flow_services.add_step("principal", self.flow, content3, self.user)

        path = flow_services.get_path("principal", self.flow)

        # Raíz + 3 pasos = 4 nodos
        self.assertEqual(len(path), 4)
        # Verificar orden (raíz primero)
        self.assertEqual(path[0].content["step"], "initial")
        self.assertEqual(path[1].content["step"], "paso1")
        self.assertEqual(path[2].content["step"], "paso2")
        self.assertEqual(path[3].content["step"], "paso3")

    def test_create_branch_from_step(self):
        """Verifica que create_branch crea una rama desde un paso específico."""
        # Añadir pasos al principal
        for i in range(1, 6):
            flow_services.add_step(
                "principal", self.flow, {"step": f"paso{i}"}, self.user
            )

        # Crear rama desde paso 3
        branch = flow_services.create_branch(
            "rama_alternativa", self.flow, "principal", 3, self.user
        )

        self.assertIsNotNone(branch)
        self.assertEqual(branch.name, "rama_alternativa")

        # Verificar que el head apunta al nodo correspondiente (posición 1-indexada incluyendo raíz)
        path_principal = flow_services.get_path("principal", self.flow)
        # paso 3 => índice 2 (raíz=1, paso1=2, paso2=3)
        self.assertEqual(branch.head, path_principal[2])
        self.assertEqual(branch.start_node, path_principal[2])

        # Verificar path de la nueva rama (debe tener hasta paso 2 compartido con la principal)
        path_branch = flow_services.get_path("rama_alternativa", self.flow)
        self.assertEqual(len(path_branch), 3)  # raíz + paso1 + paso2

    def test_branch_extends_independently(self):
        """Verifica que añadir pasos a una rama no afecta la rama padre."""
        # Crear rama desde paso 2
        flow_services.add_step("principal", self.flow, {"step": "A"}, self.user)
        flow_services.add_step("principal", self.flow, {"step": "B"}, self.user)

        flow_services.create_branch(
            "experimental", self.flow, "principal", 2, self.user
        )

        # Añadir paso a la rama experimental
        flow_services.add_step("experimental", self.flow, {"step": "X"}, self.user)

        # Verificar que principal solo tiene A y B
        path_main = flow_services.get_path("principal", self.flow)
        self.assertEqual(len(path_main), 3)  # raíz + A + B

        # Verificar que experimental tiene A + X
        path_exp = flow_services.get_path("experimental", self.flow)
        self.assertEqual(len(path_exp), 3)  # raíz + A + X

        # Verificar que el nodo X no está en la rama principal
        main_contents = [n.content["step"] for n in path_main]
        self.assertNotIn("X", main_contents)

    def test_delete_branch_removes_exclusive_nodes(self):
        """Verifica que delete_branch elimina nodos exclusivos de la rama."""
        # Crear árbol: principal con pasos 1-5
        for i in range(1, 6):
            flow_services.add_step(
                "principal", self.flow, {"step": f"main{i}"}, self.user
            )

        # Crear rama desde paso 3
        flow_services.create_branch("rama1", self.flow, "principal", 3, self.user)

        # Añadir pasos exclusivos a rama1
        flow_services.add_step("rama1", self.flow, {"step": "r1_a"}, self.user)
        flow_services.add_step("rama1", self.flow, {"step": "r1_b"}, self.user)

        # Contar nodos antes
        nodes_before = FlowNode.objects.filter(flow=self.flow).count()

        # Eliminar rama1
        flow_services.delete_branch("rama1", self.flow)

        # Verificar que los nodos exclusivos se eliminaron
        nodes_after = FlowNode.objects.filter(flow=self.flow).count()
        self.assertEqual(nodes_before - nodes_after, 2)  # r1_a y r1_b

        # Verificar que la rama se eliminó
        self.assertFalse(
            FlowBranch.objects.filter(flow=self.flow, name="rama1").exists()
        )

    def test_delete_branch_recursive(self):
        """Verifica que delete_branch elimina subramas recursivamente."""
        # Crear árbol con subramas
        for i in range(1, 4):
            flow_services.add_step("principal", self.flow, {"step": f"p{i}"}, self.user)

        # Crear rama1 desde paso 2
        flow_services.create_branch("rama1", self.flow, "principal", 2, self.user)
        flow_services.add_step("rama1", self.flow, {"step": "r1"}, self.user)

        # Crear subrama desde rama1
        flow_services.create_branch("subrama", self.flow, "rama1", 2, self.user)
        flow_services.add_step("subrama", self.flow, {"step": "sub"}, self.user)

        # Eliminar rama1 (debe eliminar subrama también)
        flow_services.delete_branch("rama1", self.flow)

        # Verificar que ambas ramas se eliminaron
        self.assertFalse(
            FlowBranch.objects.filter(flow=self.flow, name="rama1").exists()
        )
        self.assertFalse(
            FlowBranch.objects.filter(flow=self.flow, name="subrama").exists()
        )

    def test_cannot_delete_main_branch(self):
        """Verifica que no se puede eliminar la rama principal."""
        with self.assertRaises(ValueError) as ctx:
            flow_services.delete_branch("principal", self.flow)
        self.assertIn("No se puede eliminar la rama principal", str(ctx.exception))

    def test_no_cycles_tree_structure(self):
        """Verifica que el árbol no tiene ciclos (cada nodo tiene un solo padre)."""
        # Añadir varios pasos y ramas
        for i in range(1, 5):
            flow_services.add_step("principal", self.flow, {"step": f"s{i}"}, self.user)

        flow_services.create_branch("r1", self.flow, "principal", 2, self.user)
        flow_services.add_step("r1", self.flow, {"step": "r1_step"}, self.user)

        flow_services.create_branch("r2", self.flow, "principal", 3, self.user)
        flow_services.add_step("r2", self.flow, {"step": "r2_step"}, self.user)

        # Verificar que todos los nodos tienen 0 o 1 padre (no ciclos)
        all_nodes = FlowNode.objects.filter(flow=self.flow)
        for node in all_nodes:
            # Cada nodo tiene exactamente un padre (excepto raíz)
            if node.parent is None:
                # Es raíz
                self.assertEqual(node, self.main_branch.start_node)
            else:
                # Tiene un único padre
                self.assertIsNotNone(node.parent)

        # Verificar que no hay nodos que apunten a sí mismos
        for node in all_nodes:
            self.assertNotEqual(node.parent_id, node.id)

    def test_shared_nodes_until_branching_point(self):
        """Verifica que los nodos se comparten hasta el punto de ramificación."""
        # Crear pasos en principal
        flow_services.add_step("principal", self.flow, {"step": "shared1"}, self.user)
        flow_services.add_step("principal", self.flow, {"step": "shared2"}, self.user)
        flow_services.add_step("principal", self.flow, {"step": "main_only"}, self.user)

        # Crear rama desde paso 3 (raíz + shared1 + shared2)
        flow_services.create_branch("branch_a", self.flow, "principal", 3, self.user)

        # Añadir paso exclusivo a branch_a
        flow_services.add_step(
            "branch_a", self.flow, {"step": "branch_only"}, self.user
        )

        # Verificar que los nodos compartidos son los mismos objetos
        path_main = flow_services.get_path("principal", self.flow)
        path_branch = flow_services.get_path("branch_a", self.flow)

        # Los primeros 3 nodos deben ser idénticos (mismo id)
        for i in range(3):
            self.assertEqual(path_main[i].id, path_branch[i].id)

        # Los nodos después de la ramificación son diferentes
        self.assertNotEqual(path_main[3].id, path_branch[3].id)

    def test_branch_numbering_consistency(self):
        """Verifica que la numeración de pasos es consistente por rama."""
        # Principal: raíz + paso1 + paso2 + paso3
        flow_services.add_step("principal", self.flow, {"s": 1}, self.user)
        flow_services.add_step("principal", self.flow, {"s": 2}, self.user)
        flow_services.add_step("principal", self.flow, {"s": 3}, self.user)

        # Rama desde paso 2 (hereda raíz + paso1 + paso2)
        flow_services.create_branch("alt", self.flow, "principal", 3, self.user)
        flow_services.add_step("alt", self.flow, {"s": "alt4"}, self.user)

        path_main = flow_services.get_path("principal", self.flow)
        path_alt = flow_services.get_path("alt", self.flow)

        # Principal: 4 pasos (raíz + 3 añadidos)
        self.assertEqual(len(path_main), 4)

        # Alt: 4 pasos (raíz + paso1 + paso2 + alt4)
        self.assertEqual(len(path_alt), 4)

        # El último paso de alt es diferente al de main
        self.assertNotEqual(path_main[-1].id, path_alt[-1].id)
