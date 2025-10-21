from django.contrib.auth import get_user_model
from django.test import TestCase
from flows.domain.steps.interface import DataStack, StepContext, execute_step
from rest_framework.test import APIClient

User = get_user_model()


class SubstitutionAndAggregatesStepTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u5", password="p")
        self.ctx = StepContext(user=self.user, data_stack=DataStack())

    def test_generate_substitution_family_then_aggregates(self):
        # Base single molecule family from smiles
        res_base = execute_step(
            "create_reference_molecule_family",
            self.ctx,
            {"mode": "from_smiles", "name": "BaseSolo", "smiles": "CCO"},
        )
        # Substitutions: two substituents and two positions = 4 permutations
        res_sub = execute_step(
            "generate_substitution_family",
            self.ctx,
            {
                "name": "Permutas",
                "base_family_id": res_base.outputs["family_id"],
                "substituent_smiles_list": ["F", "Cl"],
                "positions": [1, 2],
            },
        )
        self.assertIn("family_id", res_sub.outputs)
        self.assertEqual(res_sub.outputs["count"], 4)

        # Now compute ADMETSA and family aggregates
        res_ag = execute_step(
            "generate_admetsa_family_aggregates",
            self.ctx,
            {"family_id": res_sub.outputs["family_id"]},
        )
        self.assertIn("saved", res_ag.outputs)
        self.assertGreater(res_ag.outputs["saved"], 0)


class SubstitutionAndAggregatesAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="api5", password="p")
        self.client.force_authenticate(self.user)

    def test_api_execute_substitution_and_aggregates(self):
        # Base single molecule family from smiles (via execute endpoint)
        payload_base = {
            "step_type": "create_reference_molecule_family",
            "params": {"mode": "from_smiles", "name": "BaseSolo2", "smiles": "CO"},
        }
        r1 = self.client.post("/api/flows/steps/execute/", payload_base, format="json")
        self.assertEqual(r1.status_code, 200)
        base_fid = r1.data["outputs"]["family_id"]

        # Step 5
        payload_sub = {
            "step_type": "generate_substitution_family",
            "params": {
                "name": "Permutas2",
                "base_family_id": base_fid,
                "substituent_smiles_list": ["Br"],
                "positions": [1, 2, 3],
            },
        }
        r2 = self.client.post("/api/flows/steps/execute/", payload_sub, format="json")
        self.assertEqual(r2.status_code, 200)
        gen_fid = r2.data["outputs"]["family_id"]
        self.assertEqual(r2.data["outputs"]["count"], 3)

        # Step 6
        payload_ag = {
            "step_type": "generate_admetsa_family_aggregates",
            "params": {"family_id": gen_fid},
        }
        r3 = self.client.post("/api/flows/steps/execute/", payload_ag, format="json")
        self.assertEqual(r3.status_code, 200)
        self.assertIn("saved", r3.data["outputs"])
