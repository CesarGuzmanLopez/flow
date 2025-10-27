from django.contrib.auth import get_user_model
from django.test import TestCase
from flows.domain.steps.interface import DataStack, StepContext, execute_step
from rest_framework.test import APIClient

User = get_user_model()


class ReferenceMoleculeFamilyStepTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u4", password="p")
        self.ctx = StepContext(user=self.user, data_stack=DataStack())

    def test_create_from_smiles(self):
        res = execute_step(
            "create_reference_molecule_family",
            self.ctx,
            {"mode": "from_smiles", "name": "RefFam", "smiles": "CCO"},
        )
        self.assertIn("family_id", res.outputs)
        self.assertEqual(res.outputs["family_name"], "RefFam")


class ReferenceMoleculeFamilyAPIExecuteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="api4", password="p")
        self.client.force_authenticate(self.user)

    def test_execute_reference_molecule_family(self):
        payload = {
            "step_type": "create_reference_molecule_family",
            "params": {"mode": "from_smiles", "name": "Solo", "smiles": "CO"},
        }
        resp = self.client.post("/api/flows/steps/execute/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("family_id", resp.data["content"]["outputs"])
