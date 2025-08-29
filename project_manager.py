import streamlit as st
import pandas as pd
import re
from openai import OpenAI
import os
import json



st.set_page_config(page_title="AI Project Management Agent", layout="wide")
st.title("🤖 AI-Powered Project Manager")


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "lm-studio"),
    base_url=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
)


team_db = pd.DataFrame([
    {"name": "Elena Rodriguez", "skills": ["Backend", "Database", "API"], "availability": "available"},
    {"name": "Liam Chen", "skills": ["Frontend", "UI/UX", "Python"], "availability": "available"},
    {"name": "Sarah Miller", "skills": ["Data Science", "ML", "Python"], "availability": "on_leave"},
    {"name": "David Lee", "skills": ["DevOps", "Cloud", "Security"], "availability": "in_meeting"},
    {"name": "Dhanush", "skills": ["DeepLearning", "GenerativeAI", "Agentic AI"], "availability": "available"},
])


project_tasks = []

def create_task_in_tool(task_data):
    """Simulates creating a task in a project management tool."""
    task_id = len(project_tasks) + 1
    task = {"id": task_id, "status": "To Do", **task_data}
    project_tasks.append(task)
    return task

def get_available_members():
    """Returns a DataFrame of team members who are currently available."""
    return team_db[team_db['availability'] == 'available']



def structure_request(unstructured_text):
    """
    Uses the AI to extract structured information from an unstructured request
    in a non-JSON, text-based format.
    """
    prompt = f"""
    Analyze the following unstructured request and extract the following information.
    Format your response as a simple text list with a clear title for each item.

    Task Title:
    Detailed Description:
    Dependencies (if any, otherwise state "None"):
    Priority (High, Medium, or Low):

    Unstructured request:
    "{unstructured_text}"
    """
    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        text_output = response.choices[0].message.content
        

        

        lines = text_output.split('\n')
        

        structured_data = {
            "title": "N/A",
            "description": "N/A",
            "dependencies": [],
            "priority": "N/A"
        }

        current_field = None
        for line in lines:
            line = line.strip()
            if line.startswith("Task Title:"):
                structured_data["title"] = line.replace("Task Title:", "").strip()
                current_field = "title"
            elif line.startswith("Detailed Description:"):
                structured_data["description"] = line.replace("Detailed Description:", "").strip()
                current_field = "description"
            elif line.startswith("Dependencies"):
                dependencies_str = line.split(":", 1)[-1].strip()
                dependencies = [dep.strip() for dep in dependencies_str.split(',') if dep.strip().lower() != 'none']
                structured_data["dependencies"] = dependencies
                current_field = "dependencies"
            elif line.startswith("Priority:"):
                structured_data["priority"] = line.replace("Priority:", "").strip()
                current_field = "priority"
            elif current_field:

                if current_field == "description":
                    structured_data["description"] += " " + line

        return structured_data

    except Exception as e:
        st.error(f"An error occurred while structuring the request: {e}")
        return None

def match_resource(task_data, team_members_df):
    """
    Uses the AI to match a task to the most suitable available team member.
    """
    task_str = json.dumps(task_data)
    team_members_str = team_members_df.to_string(index=False)
    
    prompt = f"""
    Based on the following task and the list of available team members, select the best person to assign this task to.
    
    **Task Details:**
    {task_str}
    
    **Available Team Members:**
    {team_members_str}
    
    Respond with the name of the most suitable team member and a brief reason.
    """
    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred during resource matching: {e}")
        return "Unassigned due to error"


def display_structured_task(task):
    st.subheader("✅ Task Structured Successfully")
    

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**📝 Title**")
        st.markdown("**📋 Priority**")
        st.markdown("**⛓️ Dependencies**")
        
    with col2:
        st.markdown(task['title'])

        if task['priority'].lower() == 'high':
            st.markdown(f"**🔴 {task['priority']}**")
        elif task['priority'].lower() == 'medium':
            st.markdown(f"**🟡 {task['priority']}**")
        else:
            st.markdown(f"**🟢 {task['priority']}**")
            
        if task['dependencies']:
            for dep in task['dependencies']:
                st.markdown(f"- {dep}")
        else:
            st.markdown("None")

    st.markdown("---")
    st.markdown("**Detailed Description:**")
    st.info(task['description'])


st.sidebar.header("Submit a New Request")
unstructured_request = st.sidebar.text_area(
    "Enter an unstructured task request:",
    "We need to set up a new database connection for the inventory system. It should be scalable and secure. This is urgent."
)


st.subheader("👥 Employee Details")

def format_skills(skills):
    return ' '.join([f'<span>{skill}</span>' for skill in skills])


styled_df = team_db.copy()
styled_df['skills'] = styled_df['skills'].apply(lambda s: ', '.join(s))

st.markdown("""
<style>
.stDataFrame span {
    background-color: #4a4a4a;
    color: white;
    padding: 3px 8px;
    margin: 2px;
    border-radius: 12px;
    font-size: 12px;
    white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)

st.dataframe(styled_df, use_container_width=True)
st.write("---")

if st.sidebar.button("Process with AI Agent"):
    st.info("Processing your request with the AI agent...")
    

    with st.spinner("Analyzing and structuring the task..."):
        structured_task = structure_request(unstructured_request)
    
    if structured_task:

        display_structured_task(structured_task)
        
        
        available_members = get_available_members()
        if available_members.empty:
            st.warning("No team members are currently available for assignment.")
            assignment_details = "No available members."
            assigned_name = "Unassigned"
        else:
            with st.spinner("Matching to the best resource..."):
                assignment_details = match_resource(structured_task, available_members)
            

            assigned_name = re.search(r'([A-Za-z]+\s[A-Za-z]+)', assignment_details)
            assigned_name = assigned_name.group(0) if assigned_name else "Unassigned"
        

        final_task = structured_task.copy()
        final_task['assigned_to'] = assigned_name
        
        created_task = create_task_in_tool(final_task)
        
        st.subheader("👨‍💻 Task Assigned!")
        st.success(f"Task **#{created_task['id']}** has been assigned to **{created_task['assigned_to']}**.")
        st.write("---")
        st.write("#### Assignment Details from AI:")
        st.markdown(assignment_details)
        
        st.write("---")
        st.subheader("📊 All Project Tasks")
        st.dataframe(pd.DataFrame(project_tasks))


if 'ran_once' not in st.session_state:
    st.info("Enter an unstructured request in the sidebar and click the button to see the AI agent in action.")
    st.session_state['ran_once'] = True

