import os
import sys
import unittest
from pathlib import Path

# Ensure project path is accessible
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import config
from src.classifier import classify_customer_persona
from src.rag_pipeline import LocalRAGPipeline
from src.generator import generate_adaptive_response
from src.escalator import check_escalation, contains_sensitive_keywords

class TestPersonaSupportAgent(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Initializes the database pipeline once for testing."""
        cls.pipeline = LocalRAGPipeline()
        
    def test_database_loaded(self):
        """Verify that ChromaDB collection has documents populated."""
        count = self.pipeline.collection.count()
        self.assertGreater(count, 0, "ChromaDB support database should contain indexed documents.")
        print(f"\n[OK] DB Verification: database contains {count} chunks.")

    def test_persona_classification(self):
        """Test that the classifier matches expected queries to the correct persona."""
        tests = [
            ("Explain the webhook payload signature verification steps.", "Technical Expert"),
            ("This is completely broken! I've been waiting for hours and nothing works!!!", "Frustrated User"),
            ("What is the business impact and resolution timeline for this payout delay?", "Business Executive")
        ]
        
        for query, expected_persona in tests:
            res = classify_customer_persona(query)
            self.assertEqual(res["persona"], expected_persona)
            print(f"[OK] Classifier Test: '{query[:30]}...' -> Match: {res['persona']} (Confidence: {res['confidence']})")

    def test_rag_retrieval(self):
        """Test RAG retrieval for relevant query keywords."""
        query = "bearer token authentication parameter headers"
        results = self.pipeline.retrieve_context(query, top_k=2)
        
        self.assertGreater(len(results), 0, "Should retrieve at least one chunk.")
        best_match = results[0]
        self.assertEqual(best_match["source"], "api_troubleshooting.md")
        self.assertGreaterEqual(best_match["score"], 0.40, "Retrieval score should be relatively high.")
        print(f"[OK] RAG Retrieval Test: Query: '{query}' -> Best Match: {best_match['source']} (Score: {best_match['score']})")

    def test_sensitive_escalation(self):
        """Verify that sensitive billing/legal words trigger escalation."""
        billing_query = "My invoice has duplicate charges, please issue a refund!"
        retrieved = self.pipeline.retrieve_context(billing_query, top_k=1)
        
        res = check_escalation(billing_query, "Frustrated User", [], retrieved)
        self.assertTrue(res["escalate"])
        self.assertEqual(res["reason"], "Sensitive account or billing issue")
        self.assertIn("duplicate charges", res["handoff_summary"])
        print(f"[OK] Escalation Test (Billing): Query '{billing_query[:25]}...' successfully escalated.")

    def test_low_confidence_escalation(self):
        """Verify that queries with zero relevance trigger low-confidence escalation."""
        unrelated_query = "What is the capital of France and how do I bake chocolate chip cookies?"
        retrieved = self.pipeline.retrieve_context(unrelated_query, top_k=1)
        
        res = check_escalation(unrelated_query, "Frustrated User", [], retrieved)
        self.assertTrue(res["escalate"])
        self.assertEqual(res["reason"], "Unresolved issue (Low documentation similarity)")
        print(f"[OK] Escalation Test (Low Confidence): Query '{unrelated_query[:25]}...' successfully escalated.")

    def test_consecutive_frustration_escalation(self):
        """Verify that multiple consecutive frustrated turns trigger escalation."""
        history = [
            {"role": "user", "content": "My API returns 401!", "persona": "Frustrated User"},
            {"role": "assistant", "content": "Please verify Bearer prefix."},
            {"role": "user", "content": "Still returns 401 error, why is it still broken!", "persona": "Frustrated User"},
            {"role": "assistant", "content": "Ensure you are using live keys, not test keys."},
            {"role": "user", "content": "I tried that and it's still failing! Fix this immediately!", "persona": "Frustrated User"}
        ]
        
        # Best matches so retrieval is high confidence
        context = [{"score": 0.85, "source": "api_troubleshooting.md", "text": "Bearer token details..."}]
        
        # Current message is frustrated
        current_query = "It's still failing, this is completely useless support!"
        
        res = check_escalation(current_query, "Frustrated User", history, context)
        self.assertTrue(res["escalate"])
        self.assertEqual(res["reason"], "Persistent user frustration")
        print(f"[OK] Escalation Test (Consecutive Frustration): Escalated successfully on turn 3.")

if __name__ == "__main__":
    unittest.main()
