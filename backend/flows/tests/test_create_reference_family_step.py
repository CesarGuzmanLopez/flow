from chemistry.models import Family
from django.contrib.auth import get_user_model
from django.test import TestCase
from flows.domain.steps.interface import DataStack, StepContext, execute_step
from rest_framework.test import APIClient

User = get_user_model()


class CreateReferenceFamilyStepTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.ctx = StepContext(user=self.user, data_stack=DataStack())

    def test_create_new_family_from_smiles(self):
        params = {"mode": "new", "name": "Fam A", "smiles_list": ["CCO", "CCN"]}
        result = execute_step("create_reference_family", self.ctx, params)
        self.assertIn("family_id", result.outputs)
        fam = Family.objects.get(pk=result.outputs["family_id"])
        self.assertEqual(fam.name, "Fam A")
        self.assertEqual(result.metadata["mode"], "new")

    def test_use_existing_family(self):
        # create via API first
        params = {"mode": "new", "name": "Fam B", "smiles_list": ["CCC"]}
        res = execute_step("create_reference_family", self.ctx, params)
        fid = res.outputs["family_id"]

        result = execute_step(
            "create_reference_family",
            self.ctx,
            {"mode": "existing", "family_id": fid},
        )
        self.assertEqual(result.outputs["family_id"], fid)
        self.assertEqual(result.metadata["mode"], "existing")


class StepAPIExecuteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="api", password="p")
        self.client.force_authenticate(self.user)

    def test_execute_step_endpoint(self):
        payload = {
            "step_type": "create_reference_family",
            "params": {
                "mode": "new",
                "name": "Fam C",
                "smiles_list": ["CO"],
            },
        }
        resp = self.client.post("/api/flows/steps/execute/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("content", resp.data)
        self.assertIn("outputs", resp.data["content"])
        self.assertIn("family_id", resp.data["content"]["outputs"])


class CadmaFlowCreationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="cadma", password="p")
        self.client.force_authenticate(self.user)

    def test_create_cadma1_flow(self):
        payload = {"mode": "new", "name": "Fam D", "smiles_list": ["CN"]}
        resp = self.client.post(
            "/api/flows/flows/create-cadma1/", payload, format="json"
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn("content", resp.data)
        self.assertIn("flow", resp.data["content"])
        self.assertEqual(resp.data["content"]["flow"]["name"], "CADMA 1")
