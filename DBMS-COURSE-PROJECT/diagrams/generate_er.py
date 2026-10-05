"""Generates an entity-relationship diagram for HIPCMS using Graphviz."""
import graphviz

g = graphviz.Digraph("HIPCMS_ER", format="png")
g.attr(rankdir="LR", splines="ortho", fontsize="11", fontname="Helvetica")
g.attr("node", shape="plaintext", fontname="Helvetica")

def entity(name, pk, attrs):
    rows = "".join(
        f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10">{a}</FONT></TD></TR>' for a in attrs
    )
    label = f'''<
<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">
<TR><TD BGCOLOR="#2c3e50"><FONT COLOR="white"><B>{name}</B></FONT></TD></TR>
<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10"><U>{pk}</U> (PK)</FONT></TD></TR>
{rows}
</TABLE>>'''
    g.node(name, label=label)

entity("USERS", "user_id", ["username", "role", "full_name"])
entity("CUSTOMER", "customer_id", ["name", "dob", "id_proof_number (UK)", "phone", "email (UK)"])
entity("DEPENDANT", "dependant_id", ["customer_id (FK)", "name", "relationship"])
entity("PLAN_MASTER", "plan_id", ["plan_name (UK)", "plan_type", "coverage_amount", "premium_amount"])
entity("POLICY", "policy_id", ["policy_number (UK)", "customer_id (FK)", "plan_id (FK)",
                                "sum_insured", "start_date", "end_date", "status"])
entity("PREMIUM", "premium_id", ["policy_id (FK)", "due_date", "amount_due", "status"])
entity("PAYMENT", "payment_id", ["premium_id (FK)", "payment_date", "amount_paid", "transaction_ref (UK)"])
entity("HOSPITAL", "hospital_id", ["hospital_name", "city", "network_type"])
entity("CLAIM", "claim_id", ["claim_number (UK)", "policy_id (FK)", "dependant_id (FK, null)",
                              "hospital_id (FK)", "claim_date", "claimed_amount", "status"])
entity("TREATMENT", "treatment_id", ["claim_id (FK)", "treatment_name", "diagnosis",
                                      "admission_date", "discharge_date", "treatment_cost"])
entity("CLAIM_DOCUMENT", "document_id", ["claim_id (FK)", "document_type", "file_reference"])
entity("ASSESSMENT", "assessment_id", ["claim_id (FK)", "assessor_id (FK)", "assessed_amount"])
entity("DECISION", "decision_id", ["claim_id (FK)", "decision_status", "approved_amount", "decided_by (FK)"])
entity("SETTLEMENT", "settlement_id", ["claim_id (FK, UK)", "settled_amount", "transaction_ref (UK)"])
entity("APPEAL", "appeal_id", ["claim_id (FK)", "appeal_date", "reason", "appeal_status"])

g.attr("edge", fontsize="9", fontname="Helvetica", color="#555555")

def rel(a, b, label):
    g.edge(a, b, label=label, dir="both", arrowtail="none", arrowhead="crow")

rel("CUSTOMER", "DEPENDANT", "1:N")
rel("CUSTOMER", "POLICY", "1:N")
rel("PLAN_MASTER", "POLICY", "1:N")
rel("POLICY", "PREMIUM", "1:N")
rel("PREMIUM", "PAYMENT", "1:N")
rel("POLICY", "CLAIM", "1:N")
rel("DEPENDANT", "CLAIM", "0..1:N")
rel("HOSPITAL", "CLAIM", "1:N")
rel("CLAIM", "TREATMENT", "1:N")
rel("CLAIM", "CLAIM_DOCUMENT", "1:N")
rel("CLAIM", "ASSESSMENT", "1:N")
rel("CLAIM", "DECISION", "1:N")
rel("CLAIM", "SETTLEMENT", "1:1")
rel("CLAIM", "APPEAL", "1:N")
rel("USERS", "POLICY", "1:N (issued_by)")
rel("USERS", "CLAIM", "1:N (submitted_by)")
rel("USERS", "ASSESSMENT", "1:N (assessor)")
rel("USERS", "DECISION", "1:N (decided_by)")

g.render("hipcms_er_diagram", directory="/home/claude/hims_project/diagrams", cleanup=True)
print("ER diagram generated.")
