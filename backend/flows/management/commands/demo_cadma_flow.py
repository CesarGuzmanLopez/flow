from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Demo: crea un flujo CADMA-like con 6 steps usando FlowEngine e InMemoryFlowRepository"

    def handle(self, *args, **options):
        # TODO: Crear flujo demo con datos reales
        # user, _ = User.objects.get_or_create(
        #     username="demo_user", defaults={"email": "demo@local"}
        # )
        #
        # engine = FlowEngine()
        # flow_id = engine.create_flow(
        #     name="CADMA Demo", owner=user, metadata={"demo": True}
        # )
        # print(f"Created flow {flow_id}")
        #
        # # Step 1: Family reference
        # c1 = {"step": 1, "type": "family_reference", "payload": {"family_id": "FAM-1"}}
        # cursor = engine.add_step(flow_id, c1)
        # print("Added step1", cursor)
        #
        # # Step 2: ADMETSA properties (calculate for placeholder)
        # props = mock_engine.calculate_properties("C1=CC=CC=C1")
        # c2 = {"step": 2, "type": "admet", "payload": props}
        # cursor = engine.add_step(flow_id, c2)
        # print("Added step2", cursor)
        #
        # # Step3: Generate initial molecule
        # mol = mock_engine.smiles_to_inchi("CCO")
        # c3 = {"step": 3, "type": "generate_mol", "payload": mol}
        # cursor = engine.add_step(flow_id, c3)
        # print("Added step3", cursor)
        #
        # # Step4: ADMETSA initial
        # props4 = mock_engine.calculate_properties(mol["canonical_smiles"])
        # c4 = {"step": 4, "type": "admet_init", "payload": props4}
        # cursor = engine.add_step(flow_id, c4)
        # print("Added step4", cursor)
        #
        # # Step5: Generate substitutions
        # subs = mock_engine.generate_substitutions(mol["canonical_smiles"], count=4)
        # c5 = {"step": 5, "type": "generate_subs", "payload": {"subs": subs}}
        # cursor = engine.add_step(flow_id, c5)
        # print("Added step5", cursor)
        #
        # # Step6: ADMETSA for generated
        # gen_props = [mock_engine.calculate_properties(s) for s in subs]
        # c6 = {"step": 6, "type": "admet_generated", "payload": {"gen_props": gen_props}}
        # cursor = engine.add_step(flow_id, c6)
        # print("Added step6", cursor)
        #
        # # Create a branch from step5 to explore alternative substitutions
        # branch_name = "alt-subs"
        # engine.create_branch(
        #     flow_id, from_cursor=5, branch_name=branch_name, owner=user
        # )
        # print(f"Created branch {branch_name} from cursor 5")
        #
        # # Snapshot
        # snap = engine.snapshot(flow_id)
        # print("Snapshot created with cursor", snap["cursor"])

        self.stdout.write(
            self.style.SUCCESS("Demo CADMA flow skeleton - add real data")
        )
