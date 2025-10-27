from django.contrib.auth import get_user_model
from django.test import TestCase
from flows.domain.steps.interface import DataStack, StepContext, execute_step
from rest_framework.test import APIClient

User = get_user_model()


class GenerateAdmetsaStepTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u2", password="p")
        self.ctx = StepContext(user=self.user, data_stack=DataStack())

    def test_generate_admetsa_from_family(self):
        # First create a family via step 1
        res1 = execute_step(
            "create_reference_family",
            self.ctx,
            {"mode": "new", "name": "Fam X", "smiles_list": ["CCO", "CCN"]},
        )
        fid = res1.outputs["family_id"]

        # Now generate ADMETSA
        res2 = execute_step("generate_admetsa", self.ctx, {"family_id": fid})
        self.assertIn("count", res2.outputs)
        self.assertGreaterEqual(res2.outputs["count"], 1)


class GenerateAdmetsaAPIExecuteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="api2", password="p")
        self.client.force_authenticate(self.user)
        # Pre-create a family
        ctx = StepContext(user=self.user, data_stack=DataStack())
        res = execute_step(
            "create_reference_family",
            ctx,
            {"mode": "new", "name": "Fam Y", "smiles_list": ["CO"]},
        )
        self.fid = res.outputs["family_id"]

    def test_execute_generate_admetsa(self):
        payload = {"step_type": "generate_admetsa", "params": {"family_id": self.fid}}
        resp = self.client.post("/api/flows/steps/execute/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("content", resp.data)
        self.assertIn("outputs", resp.data["content"])
        self.assertIn("count", resp.data["content"]["outputs"])
