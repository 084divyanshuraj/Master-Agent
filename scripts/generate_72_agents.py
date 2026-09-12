"""
Generate public/data/agents.json containing all 72 university hackathon agents
categorized into 4 Main Categories and 14 Sub-Categories (Groups).
"""
import re
import json
import os

DOC_PATH = r"C:\Users\Divyanshu\.gemini\antigravity-ide\brain\4e7e1127-6787-4dcd-a6c1-8bec6734a6e7\.system_generated\steps\431\content.md"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "data", "agents.json")

group_names = {
    1: "Academics Agents",
    2: "Attendance and Student Performance Agents",
    3: "Research Agents",
    4: "Extension and Outreach Agents",
    5: "Examination Agents",
    6: "Admissions Agents",
    7: "Fee and Finance Agents",
    8: "Student Affairs Agents",
    9: "Placement and Career Agents",
    10: "Policies and Governance Agents",
    11: "Faculty Management Agents",
    12: "Documentation and Reporting Agents",
    13: "Student Support Agents",
    14: "Advanced and Composite Agents",
}

group_descriptions = {
    1: "Curriculum architecture, syllabus revisions, course content repositories, faculty workload allocations, timetables, and academic performance.",
    2: "Student attendance analytics, proactive slow-learner identification, advanced learner tracks, academic risk scoring, and interventions.",
    3: "Faculty research publications across Scopus/WoS, journal quartile verification (Q1-Q4), grant proposals, patents, and PhD scholar monitoring.",
    4: "National and international conferences, AICTE/ATAL FDPs, corporate MoUs, community outreach initiatives, and alumni relations.",
    5: "End-to-end examination management, automated question paper generation, Bloom's taxonomy quality audits, internal assessments, and backlog tracking.",
    6: "Omnichannel admission enquiries, applicant counselling workflows, merit conversion analytics, and real-time document verification.",
    7: "Institutional fee collection structures, automated fee due reminders, merit-cum-means scholarships, and education loan bank liaisons.",
    8: "Holistic student portfolios, faculty mentor-mentee logs, institutional grievance redressal, student disciplinary councils, and achievements.",
    9: "Campus placement readiness diagnostics, intelligent job role matching, mandatory internship tracking, and university alumni networking.",
    10: "Statutory university policies, regulatory compliance (UGC, AICTE, NAAC, NBA), circular dissemination, and IQAC quality assurance.",
    11: "Faculty teaching and research workload distribution, annual appraisal performance scoring, faculty development records, and biometric leave tracking.",
    12: "Automated executive report generation, cross-departmental data analytics, institutional document intelligence, and accreditation exports.",
    13: "24/7 centralized student helpdesk, mental health and career counselling, digital learning resources, and professional certification audits.",
    14: "High-level institutional early warning signals, academic decision support, executive university KPI dashboards, and long-range strategic planning.",
}

category_info = {
    1: {
        "id": "category_1",
        "number": 1,
        "name": "Academic Lifecycle & Faculty Governance",
        "badge": "20 Specialized Agents",
        "description": "Comprehensive academic operations: curriculum architecture, syllabus audits, exam management, question paper generation, grading analytics, and faculty workload governance.",
        "groups": [1, 5, 11]
    },
    2: {
        "id": "category_2",
        "number": 2,
        "name": "Student Success, Admissions & Support Services",
        "badge": "23 Specialized Agents",
        "description": "The complete student journey: admissions intake, biometric attendance, risk modeling, fee & scholarship financing, student mentoring, grievances, and helpdesk support.",
        "groups": [2, 6, 7, 8, 13]
    },
    3: {
        "id": "category_3",
        "number": 3,
        "name": "Research, Industry Partnerships & Career Placements",
        "badge": "17 Specialized Agents",
        "description": "University innovation ecosystem: Scopus/WoS publication tracking, journal quartiles, patents, funding grants, corporate MoUs, internships, and campus recruitment.",
        "groups": [3, 4, 9]
    },
    4: {
        "id": "category_4",
        "number": 4,
        "name": "Institutional Strategy, IQAC & Analytics Intelligence",
        "badge": "12 Specialized Agents",
        "description": "Executive decision support: university governance policies, statutory compliance, NAAC/NBA criteria reporting, cross-departmental analytics, and institutional KPI modeling.",
        "groups": [10, 12, 14]
    }
}

agent_to_group = {}
for i in range(1, 11): agent_to_group[i] = 1
for i in range(11, 17): agent_to_group[i] = 2
for i in range(17, 26): agent_to_group[i] = 3
for i in range(26, 30): agent_to_group[i] = 4
for i in range(30, 36): agent_to_group[i] = 5
for i in range(36, 40): agent_to_group[i] = 6
for i in range(40, 44): agent_to_group[i] = 7
for i in range(44, 49): agent_to_group[i] = 8
for i in range(49, 53): agent_to_group[i] = 9
for i in range(53, 58): agent_to_group[i] = 10
for i in range(58, 62): agent_to_group[i] = 11
for i in range(62, 65): agent_to_group[i] = 12
for i in range(65, 69): agent_to_group[i] = 13
for i in range(69, 73): agent_to_group[i] = 14

def group_to_category(grp_num):
    for cat_num, cat in category_info.items():
        if grp_num in cat["groups"]:
            return cat_num
    return 1

with open(DOC_PATH, "r", encoding="utf-8") as f:
    raw_doc = f.read()

part_b = raw_doc[raw_doc.find("Part B — Agent Catalogue"):]

def make_slug(name):
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", name).strip().lower()
    return re.sub(r"[\s-]+", "-", slug)

agents_dict = {}

for num in range(1, 73):
    pattern = rf"Agent\s+{num}\.\s+([^\n\r]+)"
    matches = list(re.finditer(pattern, part_b))
    chosen = None
    for cand in matches:
        following = part_b[cand.end():cand.end()+300]
        if "Purpose." in following:
            chosen = cand
            break
    if not chosen and matches:
        chosen = matches[-1]
    
    if not chosen:
        print(f"WARNING: Could not find header for Agent {num}")
        continue
    
    agent_name = chosen.group(1).strip()
    following_text = part_b[chosen.end():chosen.end()+2500]
    
    # Extract Purpose
    p_match = re.search(r"Purpose\.\s*(.+?)(?=(Primary users\.|Inputs\.|Workflow\.|Outputs\.|Failure modes\.|\n\n[A-Z]|$))", following_text, re.DOTALL)
    purpose = p_match.group(1).strip() if p_match else "Operational agent for university workflows."
    purpose = re.sub(r"\s+", " ", purpose)
    
    # Extract Primary users
    u_match = re.search(r"Primary users\.\s*(.+?)(?=(Inputs\.|Workflow\.|Outputs\.|Failure modes\.|\n\n|$))", following_text, re.DOTALL)
    primary_users = u_match.group(1).strip() if u_match else "University Deans, HoDs, and Faculty."
    primary_users = re.sub(r"\s+", " ", primary_users)
    
    # Extract Inputs
    in_match = re.search(r"Inputs\.\s*(.+?)(?=(Workflow\.|Outputs\.|Failure modes\.|\n\n|$))", following_text, re.DOTALL)
    inputs = in_match.group(1).strip() if in_match else "Institutional databases and university records."
    inputs = re.sub(r"\s+", " ", inputs)
    
    # Extract Outputs
    out_match = re.search(r"Outputs\.\s*(.+?)(?=(Failure modes\.|\n\n|$))", following_text, re.DOTALL)
    outputs = out_match.group(1).strip() if out_match else "Verified analytical reports and automated service actions."
    outputs = re.sub(r"\s+", " ", outputs)

    grp_num = agent_to_group[num]
    cat_num = group_to_category(grp_num)
    slug = make_slug(agent_name)
    
    sample_prompts = [
        f"Generate latest status report for {agent_name}",
        f"Query institutional records via {agent_name}",
        f"Audit compliance metrics for {agent_name}"
    ]

    agents_dict[num] = {
        "id": f"agent_{num:02d}",
        "number": num,
        "name": agent_name,
        "group_id": f"group_{grp_num}",
        "group_number": grp_num,
        "group_name": group_names[grp_num],
        "category_id": f"category_{cat_num}",
        "category_number": cat_num,
        "category_name": category_info[cat_num]["name"],
        "description": purpose,
        "primary_users": primary_users,
        "inputs": inputs,
        "outputs": outputs,
        "endpoint_url": f"https://api.vignan.ac.in/agents/{slug}",
        "deployment_url": f"https://api.vignan.ac.in/agents/{slug}",
        "sample_prompts": sample_prompts,
        "status": "online"
    }

# Build structured hierarchy
final_groups = []
for g_num in range(1, 15):
    g_agents = [agents_dict[num] for num in sorted(agents_dict.keys()) if agents_dict[num]["group_number"] == g_num]
    c_num = group_to_category(g_num)
    final_groups.append({
        "id": f"group_{g_num}",
        "group_number": g_num,
        "category_id": f"category_{c_num}",
        "category_number": c_num,
        "category_name": category_info[c_num]["name"],
        "name": group_names[g_num],
        "description": group_descriptions[g_num],
        "total_agents": len(g_agents),
        "agents": g_agents
    })

final_categories = []
for c_num in range(1, 5):
    cat_spec = category_info[c_num]
    c_groups = [g for g in final_groups if g["category_number"] == c_num]
    total_cat_agents = sum(g["total_agents"] for g in c_groups)
    final_categories.append({
        "id": cat_spec["id"],
        "category_number": c_num,
        "name": cat_spec["name"],
        "badge": f"{total_cat_agents} Specialized Agents",
        "description": cat_spec["description"],
        "total_agents": total_cat_agents,
        "groups": c_groups
    })

output_data = {
    "platform": "Vignan's Foundation for Science, Technology & Research",
    "portal_title": "Enterprise Master Agent Orchestration Network",
    "total_agents": len(agents_dict),
    "total_categories": len(final_categories),
    "total_groups": len(final_groups),
    "categories": final_categories,
    "groups": final_groups
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"Successfully generated {OUTPUT_PATH} with {len(agents_dict)} agents across {len(final_categories)} categories and {len(final_groups)} groups.")
