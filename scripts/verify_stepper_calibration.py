import re
from pathlib import Path

EXAMPLES_VIEW = Path("examples_view")

PILLARS = [
    {
        "file": EXAMPLES_VIEW / "phasing" / "basic.html",
        "name": "basic",
        "expected_steps": 5,
        "keywords": ["Top-Down", "Bottom-Up", "Objection", "Time Progression", "Cleanup"]
    },
    {
        "file": EXAMPLES_VIEW / "phasing" / "objections.html",
        "name": "objections",
        "expected_steps": 5,
        "keywords": ["Drain Time", "Forking", "Dropping", "Drain Trigger", "Expiration"]
    },
    {
        "file": EXAMPLES_VIEW / "tlm-1" / "fifo.html",
        "name": "fifo",
        "expected_steps": 5,
        "keywords": ["TLM Port", "Burst Fill", "Back-Pressure", "Extraction", "Producer Resume"]
    },
    {
        "file": EXAMPLES_VIEW / "tlm-2" / "nonblocking_simple.html",
        "name": "nonblocking_simple",
        "expected_steps": 4,
        "keywords": ["BEGIN_REQ", "Payload Transfer", "Backward Path", "UVM_TLM_COMPLETED"]
    },
    {
        "file": EXAMPLES_VIEW / "registers" / "primer.html",
        "name": "primer",
        "expected_steps": 4,
        "keywords": ["model.write", "reg2bus", "Hardware Bus", "Mirror Check"]
    }
]

def verify_all():
    print("=" * 60)
    print("  Verifying Test Scenario Walkthrough Calibration")
    print("=" * 60)
    
    all_ok = True
    for p in PILLARS:
        path = p["file"]
        if not path.exists():
            print(f"  [FAIL] {path} does not exist!")
            all_ok = False
            continue
            
        content = path.read_text(encoding="utf-8")
        
        # Check stepper section
        if "visual-flow-stepper" not in content:
            print(f"  [FAIL] {p['name']}: visual-flow-stepper missing")
            all_ok = False
            continue
            
        # Check scenario-state-pill
        if "scenario-state-pill" not in content:
            print(f"  [FAIL] {p['name']}: scenario-state-pill missing")
            all_ok = False
            continue

        # Check visual concept animation container
        if "scenario-anim-section" not in content or f'data-anim="{p["name"] if p["name"] != "primer" and p["name"] != "basic" and p["name"] != "nonblocking_simple" else ("ral" if p["name"] == "primer" else ("phasing" if p["name"] == "basic" else "tlm2"))}"' not in content:
            print(f"  [FAIL] {p['name']}: scenario-anim-section or matching data-anim missing")
            all_ok = False
            continue

        # Check jump buttons
        if "btn-jump-code" not in content or "btn-jump-log" not in content:
            print(f"  [FAIL] {p['name']}: jump buttons missing")
            all_ok = False
            continue

        # Check step nodes count
        nodes = re.findall(r'class="step-node[^"]*"', content)
        if len(nodes) != p["expected_steps"]:
            print(f"  [FAIL] {p['name']}: expected {p['expected_steps']} step nodes, got {len(nodes)}")
            all_ok = False
            continue

        # Check keywords
        for kw in p["keywords"]:
            if kw.lower() not in content.lower():
                print(f"  [FAIL] {p['name']}: missing expected keyword '{kw}'")
                all_ok = False
                break
        else:
            print(f"  [PASS] {p['name']}: verified {len(nodes)} calibrated steps with state badges and jump controls")

    print("=" * 60)
    if all_ok:
        print("  All Test Scenario Walkthroughs calibrated and verified!")
    else:
        print("  Calibration verification failed.")
    print("=" * 60)
    return all_ok

if __name__ == "__main__":
    import sys
    sys.exit(0 if verify_all() else 1)

