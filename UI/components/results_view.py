import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

def load_test_results(supabase, test_id: str = None):
    """Load test results from database"""
    try:
        query = supabase.table("submissions").select("*")
        if test_id:
            query = query.eq("test_id", test_id)
        
        results = query.execute()
        return results.data
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")
        return []

def format_datetime(dt_str: str) -> str:
    """Format datetime string to readable format"""
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.strftime("%Y-%m-%d %H:%M")

def show_results_tab(supabase):
    """Show results tab with test submissions"""
    st.title("Test Results")
    
    # Load all tests for filter
    tests = supabase.table("tests").select("id, title, access_code").execute()
    test_options = {f"{t['title']} ({t['access_code']})": t['id'] for t in tests.data}
    test_options["All Tests"] = None
    
    # Filter by test
    selected_test_name = st.selectbox(
        "Select Test",
        options=list(test_options.keys()),
        index=0
    )
    selected_test_id = test_options[selected_test_name]
    
    # Load results
    results = load_test_results(supabase, selected_test_id)
    
    if not results:
        st.info("No results to display")
        return
        
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(results)
    df['submitted_at'] = pd.to_datetime(df['submitted_at'])
    df['formatted_date'] = df['submitted_at'].dt.strftime("%Y-%m-%d %H:%M")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Attempts", len(df))
    with col2:
        avg_score = df['percentage'].mean()
        st.metric("Average Score", f"{avg_score:.1f}%")
    with col3:
        passing_rate = (df['percentage'] >= 60).mean() * 100
        st.metric("Pass Rate (≥60%)", f"{passing_rate:.1f}%")
    with col4:
        unique_students = df['student_name'].nunique()
        st.metric("Unique Students", unique_students)
    
    # Graphs tab and table tab
    tab1, tab2 = st.tabs(["📊 Graphs", "📋 Results Table"])
    
    with tab1:
        # Score distribution
        fig_hist = px.histogram(
            df, 
            x='percentage',
            title='Score Distribution',
            labels={'percentage': 'Score Percentage', 'count': 'Number of Students'},
            nbins=20
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Time series of scores
        fig_time = px.scatter(
            df,
            x='submitted_at',
            y='percentage',
            title='Scores Over Time',
            labels={'submitted_at': 'Submission Time', 'percentage': 'Score Percentage'}
        )
        st.plotly_chart(fig_time, use_container_width=True)
        
        # Question analysis
        if selected_test_id:
            st.subheader("Question Analysis")
            question_stats = {}
            
            for submission in results:
                detailed = submission.get('detailed_answers', {})
                for q_id, q_data in detailed.items():
                    if q_id not in question_stats:
                        question_stats[q_id] = {
                            'text': q_data['question_text'],
                            'correct': 0,
                            'total': 0,
                            'order': q_data['order_number']
                        }
                    question_stats[q_id]['total'] += 1
                    if q_data['is_correct']:
                        question_stats[q_id]['correct'] += 1
            
            # Convert to DataFrame and calculate percentages
            q_df = pd.DataFrame([
                {
                    'Number': stats['order'],
                    'Question': stats['text'],
                    'Correct Percentage': (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                }
                for stats in question_stats.values()
            ]).sort_values('Number')
            
            fig_questions = px.bar(
                q_df,
                x='Number',
                y='Correct Percentage',
                title='Question Statistics',
                labels={'Correct Percentage': '% Correct Answers'}
            )
            st.plotly_chart(fig_questions, use_container_width=True)
    
    with tab2:
        # Detailed results table
        st.subheader("Detailed Results")
        
        # Search by student name
        search_name = st.text_input("🔍 Search by Student Name").strip().lower()
        
        # Filter by date
        col1, col2 = st.columns(2)
        with col1:
            min_date = df['submitted_at'].min().date()
            start_date = st.date_input("From", min_date)
        with col2:
            max_date = df['submitted_at'].max().date()
            end_date = st.date_input("To", max_date)
        
        # Apply filters
        mask = (df['submitted_at'].dt.date >= start_date) & (df['submitted_at'].dt.date <= end_date)
        if search_name:
            mask = mask & df['student_name'].str.lower().str.contains(search_name)
        
        filtered_df = df[mask].copy()
        
        # Sort options
        sort_col = st.selectbox(
            "Sort by",
            options=["Date (Newest)", "Date (Oldest)", "Name", "Score (Highest)", "Score (Lowest)"]
        )
        
        if sort_col == "Date (Newest)":
            filtered_df = filtered_df.sort_values('submitted_at', ascending=False)
        elif sort_col == "Date (Oldest)":
            filtered_df = filtered_df.sort_values('submitted_at', ascending=True)
        elif sort_col == "Name":
            filtered_df = filtered_df.sort_values('student_name')
        elif sort_col == "Score (Highest)":
            filtered_df = filtered_df.sort_values('percentage', ascending=False)
        else:
            filtered_df = filtered_df.sort_values('percentage', ascending=True)
        
        # Display results
        for _, row in filtered_df.iterrows():
            with st.expander(f"📝 {row['student_name']} - {row['percentage']}% ({row['formatted_date']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Correct Answers", f"{row['score']}/{row['total_questions']}")
                with col2:
                    st.metric("Score", f"{row['percentage']}%")
                
                # Show detailed answers if available
                if 'detailed_answers' in row and row['detailed_answers']:
                    st.write("### Question Details")
                    for q_id, q_data in sorted(
                        row['detailed_answers'].items(),
                        key=lambda x: x[1]['order_number']
                    ):
                        if q_data['is_correct']:
                            st.success(f"✅ {q_data['question_text']}")
                            st.write(f"Answer: {q_data['student_answer']}")
                        else:
                            st.error(f"❌ {q_data['question_text']}")
                            st.write(f"Student's Answer: {q_data['student_answer']}")
                            st.write(f"Correct Answer: {q_data['correct_answer']}")
                        st.markdown("---")
