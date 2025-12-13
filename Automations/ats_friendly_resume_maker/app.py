import streamlit as st
import os
from fpdf import FPDF
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
import json
import re

load_dotenv()
# Initialize the Gemini Client
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model_name = 'gemini-2.5-flash' # A great model for fast text generation
except Exception as e:
    st.error(f"Error initializing Gemini client. Make sure the GEMINI_API_KEY is set. Details: {e}")
    client = None
resume_content = """
RESUME_CONTENT
"""
# --- 2. GEMINI API CALL FUNCTION ---

def get_optimized_resume(resume_content: str, jd_content: str, prompt_template: str):
    """
    Calls the Gemini API to get the optimized resume content.
    """
    if not client:
        return {"error": "Gemini Client not initialized. Check API Key configuration."}

    # Construct the full prompt by substituting the user inputs
    full_prompt = prompt_template.replace("[PASTE RESUME CONTENT HERE]", "```"+resume_content+"```")
    full_prompt = full_prompt.replace("[PASTE JD CONTENT HERE]", "```"+jd_content+"```")

    try:
        with st.spinner("🤖 Optimizing your resume with Gemini..."):
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            # print(f"Raw response: {response.text}") # Debugging

            # Extract JSON from markdown code block if present
            raw_text = response.text
            json_match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
            if json_match:
                json_string = json_match.group(1)
            else:
                # Try to find the first { and last }
                start_idx = raw_text.find('{')
                end_idx = raw_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_string = raw_text[start_idx:end_idx+1]
                else:
                    json_string = raw_text

            # Attempt to parse the JSON response
            try:
                structured_response = json.loads(json_string)
                return structured_response
            except json.JSONDecodeError:
                st.error("The model did not return a valid JSON response.")
                return {"error": "Invalid JSON response from model", "raw_response": raw_text}

    except APIError as e:
        st.error(f"Gemini API Error: {e}")
        return {"error": f"Failed to generate content due to an API issue: {e}"}
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return {"error": f"An unexpected error occurred during generation: {e}"}# --- 3. STREAMLIT UI ---

def main():
    st.set_page_config(
        page_title="Resume ATS Optimizer with Gemini",
        page_icon="✍️",
        layout="wide"
    )

    st.title("✍️ Resume ATS Optimizer")
    st.markdown("Use the power of Gemini to rewrite your resume for a specific Job Description, maximizing your **ATS match score**.")

    # Define the core prompt template provided by the user
    # Note: Using triple quotes for multi-line string clarity
    OPTIMIZATION_PROMPT = """
**Role:**
Act as a Senior Resume Writer & ATS Algorithm Expert.
Your ONLY goal is to maximize the ATS Match Score (>90%) for the provided Resume against the provided Job Description (JD).

**Inputs:**
* **Resume:** [PASTE RESUME CONTENT HERE]
* **Job Description:** [PASTE JD CONTENT HERE]

**HARDCODED CANDIDATE PROJECT PORTFOLIO (SOURCE OF TRUTH):**
Use ONLY these projects. Do NOT invent others.
[PROVIDE YOUR PROJECT DETAILS HERE]

**STRATEGY FOR MAXIMUM SCORE:**
1.  **Bridge the Gap:** Select 2-3 projects from the list above that best match the JD's requirements. Contextualize the bullet points (e.g. if JD says "Forensic Data", and you pick "Data Quality", say "ensured forensic data quality").
2.  **Clean Skills:** Ensure "Technical Skills" only contains valid technologies.

**EXECUTION RULES (Strict):**

1.  **Project Selection:**
    *   Select **2-3 projects** from the Hardcoded List.
    *   **NO FABRICATION:** Use the official Title and Tech Stack.
    *   **METRICS:** Add plausible metrics to the description bodies.

2.  **Technical Skills (CRITICAL):**
    *   **Technical Skills:** ONLY hard tech (Python, SQL, GCP, Docker, etc) and tools and it should be concise and not too long.
    *   **NO DOMAIN TERMS:** Do NOT include soft skills or domain theories like "Economics", "Strategy", or "Regulation" in this section.

3.  **Preserve Core Content:**
    *   **Work Experience:** Keep structure identical. Lightly polish verbs.
    *   **Certifications:** Keep identical.

4.  **Job Title:**
    *   Use the TARGET Job Title from the JD, but REMOVE any location.

5.  **JSON Structure:**
    ```json
    {
        "name": "Candidate Name",
        "title": "Clean Job Title",
        "contact_info": "Phone | Email | LinkedIn | Location",
        "summary": "Rich summary...",
        "technical_skills": {
            "Cloud Platforms": "",
            "Data Engineering & Orchestration": "",
            "Programming Languages": "",
            "DevOps & IaC": "",
            "AI/ML & Analytics": "",
            "Databases & Warehousing": "",
            "Operating Systems": "Linux.",
        },
        "professional_experience": [
            {
                "company": "Company",
                "role": "Role",
                "duration": "Dates",
                "responsibilities": [
                    "Bullet 1 (Polished)",
                    "Bullet 2 (Polished)"
                ]
            }
        ],
        "projects": [
            {
                "name": "Project Name (From List)",
                "tech_stack": "Tech Stack (From List)",
                "details": [
                   "Bullet 1 (Contextualized + Metrics)",
                   "Bullet 2 (Contextualized + Metrics)"
                ]
            }
        ],
        "education": [
            {
                "degree": "Degree",
                "university": "University",
                "graduation_year": "Year"
            }
        ],
        "certifications": [
            "Cert Name (Keep Original)"
        ]
    }
    ```

6.  **Output Restriction:**
    *   Return ONLY valid JSON.
"""

    # --- Input Columns ---
    st.subheader("Target Job Description (JD)")
    jd_input = st.text_area(
            "Paste the job description text here:",
            height=100,
            value="INPUT JOB DESCRIPTION HERE")

    st.markdown("---")

    # --- Optimization Button ---

    if st.button("🚀 Optimize Resume", type="primary", use_container_width=True):
        if not jd_input:
            st.error("Please provide content for the Job Description.")
            return

        # Call the function to get the optimized content
        optimized_content = get_optimized_resume(resume_content, jd_input, OPTIMIZATION_PROMPT)

        # --- Output Section ---
        st.subheader("✨ Optimized Resume Content (PDF Preview)")
        
        if "error" in optimized_content:
            st.error(optimized_content["error"])
            if "raw_response" in optimized_content:
                st.text_area("Raw Model Response (for debugging)", optimized_content["raw_response"], height=200)
            return
        
        def build_pdf_from_json(data):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Register a full UTF-8 compatible font (replace path if needed)
            # Use a fallback if fonts are not found, or assume they are there as per file listing
            try:
                pdf.add_font("DejaVu", "", "/app/DejaVuSans.ttf", uni=True)
                pdf.add_font("DejaVu", "B", "/app/DejaVuSans-Bold.ttf", uni=True)
                pdf.add_font("DejaVu", "I", "/app/DejaVuSans-Oblique.ttf", uni=True)
                font_family = "DejaVu"
            except:
                font_family = "Arial" # Fallback

            # Add Photo if exists
            if os.path.exists("/app/photo.jpg"):
                 # x=10 (left margin), y=10, w=25 (passport size-ish)
                 # Adjust positions to not overlap with centered text if needed, 
                 # but centered text creates a header. 
                 # We'll put it in the top left corner.
                 pdf.image("/app/photo.jpg", x=10, y=10, w=25)

            # Default font
            pdf.set_font(font_family, size=10)

            # ---- NAME & TITLE ----
            # Logic: If photo exists (w=25, x=10), text should start after it (x>35) to avoid overlap.
            # We'll set x=40 for safety and center within the remaining width.
            
            photo_offset = 0
            if os.path.exists("photo.jpg"):
                photo_offset = 30 # 10 margin + 25 photo - 5 overlap fix? No, 10+25=35. Let's say 40.
            
            # Reposition Cursor
            pdf.set_y(15) 

            # NAME
            if photo_offset > 0:
                pdf.set_x(10 + 25 + 5) # Start after photo
            pdf.set_font(font_family, "B", 24)
            # cell(0) goes to right margin. If we set x, it goes from x to right margin.
            # align='C' centers it in that space.
            pdf.cell(0, 12, data.get("name", ""), ln=True, align='L' if photo_offset>0 else 'C')

            # TITLE (Handle long titles with multi_cell)
            if photo_offset > 0:
                pdf.set_x(10 + 25 + 5)
            pdf.set_font(font_family, "B", 16)
            
            # Multi_cell doesn't automatically go to right margin with width=0 if x is changed?
            # Actually fpdf docs say w=0 means "right margin".
            # Try Left alignment if photo exists to look cleaner next to it? 
            # Or Center relative to remaining space?
            # User said "going behind photo". 
            # Let's try Align 'L' (Left) next to photo. It usually looks professional.
            # Or 'C' if they prefer centered. Let's stick to 'L' to definitely avoid overlap confusion.
            pdf.multi_cell(0, 10, data.get("title", ""), align='L' if photo_offset>0 else 'C')

            # ---- CONTACT INFO ----
            # This might also need shifting if it's high up.
            # Usually it's below title.
            if photo_offset > 0:
                 pdf.set_x(10 + 25 + 5)
            pdf.set_font(font_family, "", 10)
            pdf.multi_cell(0, 6, data.get("contact_info", ""), align='L' if photo_offset>0 else 'C')
            pdf.ln(5)

            # ----------------------------
            # SECTION: Professional Summary
            # ----------------------------
            if data.get("summary"):
                pdf.set_font(font_family, "BU", 12)
                pdf.cell(0, 8, "PROFESSIONAL SUMMARY", ln=True)

                pdf.set_font(font_family, "", 10)
                pdf.multi_cell(0, 5, data["summary"])
                pdf.ln(5)
            # ----------------------------
            # SECTION: Professional Experience
            # ----------------------------
            if data.get("professional_experience"):
                pdf.set_font(font_family, "BU", 12)
                pdf.cell(0, 8, "WORK EXPERIENCE", ln=True)

                for job in data["professional_experience"]:
                    pdf.set_font(font_family, "B", 10)
                    pdf.multi_cell(0, 6, f"{job.get('company', '')} | {job.get('role', '')}")

                    pdf.set_font(font_family, "I", 9)
                    pdf.cell(0, 5, job.get("duration", ""), ln=True)

                    pdf.set_font(font_family, "", 10)
                    for resp in job.get("responsibilities", []):
                        pdf.multi_cell(0, 5, "• " + resp)

                    pdf.ln(2)
                pdf.ln(2)

            # ----------------------------
            # SECTION: Technical Skills
            # ----------------------------
            if data.get("technical_skills"):
                pdf.set_font(font_family, "BU", 12)
                pdf.cell(0, 8, "TECHNICAL SKILLS", ln=True)

                for category, skills in data["technical_skills"].items():
                    # Bold label
                    pdf.set_font(font_family, "B", 10)
                    pdf.write(6, f"{category}: ")
                    # Normal text for skills
                    pdf.set_font(font_family, "", 10)
                    # Handle if skills is list or string
                    if isinstance(skills, list):
                        skills_str = ", ".join(skills)
                    else:
                        skills_str = str(skills)
                    pdf.write(6, skills_str)

                    pdf.ln(5)
                pdf.ln(2)

            # ----------------------------
            # SECTION: Education
            # ----------------------------
            if data.get("education"):
                pdf.set_font(font_family, "BU", 12)
                pdf.cell(0, 8, "EDUCATION", ln=True)

                for edu in data["education"]:
                    pdf.set_font(font_family, "B", 10)
                    pdf.cell(0, 6, edu.get("degree", ""), ln=True)

                    pdf.set_font(font_family, "", 10)
                    pdf.cell(0, 5, f"{edu.get('university', '')} | {edu.get('graduation_year', '')}", ln=True)
                    pdf.ln(2)

                pdf.ln(2)
            
            # ----------------------------
            # SECTION: Key Projects
            # ----------------------------
            if data.get("projects"):
                pdf.set_font(font_family, "BU", 12)
                pdf.cell(0, 8, "KEY PROJECTS", ln=True)

                for proj in data["projects"]:
                    # Project Name
                    pdf.set_font(font_family, "B", 10)
                    pdf.multi_cell(0, 6, proj.get("name", "Project"))
                    
                    # Tech Stack (if available)
                    if proj.get("tech_stack"):
                        pdf.set_font(font_family, "I", 9)
                        pdf.multi_cell(0, 5, f"Tech Stack: {proj.get('tech_stack')}")

                    # Bullets
                    pdf.set_font(font_family, "", 10)
                    for detail in proj.get("details", []):
                         pdf.multi_cell(0, 5, "• " + detail)
                    
                    pdf.ln(3)
                pdf.ln(2)

            # ----------------------------
            # SECTION: Certifications
            # ----------------------------
            if data.get("certifications"):
                pdf.set_font(font_family, "BU", 12)
                pdf.cell(0, 8, "CERTIFICATIONS", ln=True)

                pdf.set_font(font_family, "", 10)
                for cert in data["certifications"]:
                     # If cert is just a string
                    pdf.multi_cell(0, 5, "• " + str(cert))
                pdf.ln(3)

                pdf.ln(2)
            
            # ----------------------------
            # SECTION: Hidden ATS Keywords (White Text)
            # # ----------------------------
            # if data.get("ats_keywords_dump"):
            #     # Move to bottom of page approx
            #     # Or just append. Since it's white, it won't be seen. 
            #     # But to be safe, small font at the end.
            #     pdf.set_text_color(255, 255, 255) # White
            #     pdf.set_font(font_family, "", 1) # Tiny font
            #     pdf.write(2, data.get("ats_keywords_dump"))
            #     # Reset color just in case (though we are done)
            #     pdf.set_text_color(0, 0, 0)

            # Return raw PDF bytes
            return pdf.output(dest="S").encode("latin1")

        pdf_bytes = build_pdf_from_json(optimized_content)

        st.download_button(
            label="💾 Download Optimized Resume (PDF)",
            data=pdf_bytes,
            file_name="Resume_Ram_Shankar_2025.pdf",
            mime="application/pdf",
            key="download_pdf_button",
        )

        st.info("The optimized resume is now available for download as a PDF.")


if __name__ == "__main__":
    main()