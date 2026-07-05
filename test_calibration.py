import json
import urllib.request

URL = "http://127.0.0.1:5000/submit"

# The 4 Explicit Validation Items required by Milestone 4
test_cases = [
    {
        "name": "1. Unedited Machine-Generated Baseline",
        "text": "Furthermore, it is important to note that the paradigm shift in software development presents significant advantages. Therefore, developers must optimize structures. Consequently, efficiency increases.",
        "creator_id": "test_bot_1"
    },
    {
        "name": "2. Informal Human Text",
        "text": "Honestly i think this whole thing is pretty cool lol. Just writing some random thoughts down here. Super fast, short sentences. Then out of nowhere i might write an incredibly long sentence just to mess with the sentence variance math engine!",
        "creator_id": "human_writer_1"
    },
    {
        "name": "3. Rigid Human Academic Text (Divergence Test)",
        "text": "The experimental data indicates a correlation between algorithmic optimization and processing latency. Consequently, the researchers concluded that architectural enhancements remain critical. Moreover, empirical evidence supports this paradigm.",
        "creator_id": "esl_academic_human"
    },
    {
        "name": "4. AI Output Manually Rewritten with Casual Variations",
        "text": "Artificial intelligence alters software engineering parameters heavily. But hey, it's not perfect. Mistakes happen all the time, you know? Regardless, it completely changes how we write applications today.",
        "creator_id": "ai_editor_human"
    }
]


def run_tests():
    print("=" * 70)
    print("PROVENANCE GUARD: MILESTONE 4 CALIBRATION SYSTEM ANALYSIS")
    print("=" * 70)

    for case in test_cases:
        print(f"\n🚀 Running: {case['name']}")
        payload = json.dumps({"text": case["text"], "creator_id": case["creator_id"]}).encode("utf-8")

        req = urllib.request.Request(
            URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                print(f"  🔹 Verdict:    {res_data.get('attribution')}")
                print(f"  🔹 Confidence: {res_data.get('confidence')}")
                print(f"  🔹 UX Label:   {res_data.get('label')}")
        except Exception as e:
            print(f"  ❌ Request Failed: {e}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_tests()