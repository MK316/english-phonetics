import pandas as pd
import streamlit as st
import random
import io

# --- Grouping Tab ---
with tabs[2]:
    st.subheader("👥 Grouping Tool")
    st.caption("Your CSV should have at least the columns `Course`, `SID`, and `Name_ori`.")

    default_url = "https://raw.githubusercontent.com/MK316/Digital-Literacy-Class/refs/heads/main/data/s25dl-roster.csv"
    st.markdown(f"[📎 Sample File: S25DL-roster.csv]({default_url})")

    uploaded_file = st.file_uploader("Upload your CSV file (optional)", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        source_label = "✅ File uploaded"
    else:
        df = pd.read_csv(default_url)
        source_label = "📂 Using default GitHub data"

    if all(col in df.columns for col in ['Course', 'Name_ori']):
        st.success(source_label)

        # Step 1: Select Course
        course_list = df['Course'].dropna().unique().tolist()
        selected_course = st.selectbox("📘 Select Course for Grouping", course_list)

        # Step 2: Group size input
        st.markdown("### 💡 Group Settings")
        num_group3 = st.number_input("Number of 3-member groups", min_value=0, step=1)
        num_group4 = st.number_input("Number of 4-member groups", min_value=0, step=1)

        if st.button("Generate Groups"):
            # Filter by course
            course_df = df[df['Course'] == selected_course]
            names = course_df['Name_ori'].dropna().tolist()
            random.shuffle(names)

            total_needed = num_group3 * 3 + num_group4 * 4

            if total_needed > len(names):
                st.error(f"❗ Not enough students in {selected_course}. Requested {total_needed}, available {len(names)}.")
            else:
                grouped_data = []
                group_num = 1

                # Make 3-member groups
                for _ in range(num_group3):
                    members = names[:3]
                    names = names[3:]
                    grouped_data.append([f"Group {group_num}"] + members)
                    group_num += 1

                # Make 4-member groups
                for _ in range(num_group4):
                    members = names[:4]
                    names = names[4:]
                    grouped_data.append([f"Group {group_num}"] + members)
                    group_num += 1

                # Prepare final DataFrame
                max_members = max(len(group) - 1 for group in grouped_data)
                columns = ['Group'] + [f'Member{i+1}' for i in range(max_members)]
                grouped_df = pd.DataFrame(grouped_data, columns=columns)

                st.success(f"✅ {selected_course}: Grouping complete!")
                st.write(grouped_df)

                # Download button
                csv_buffer = io.StringIO()
                grouped_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Download Grouped CSV",
                    data=csv_buffer.getvalue().encode('utf-8'),
                    file_name=f"grouped_{selected_course.replace(' ', '_')}.csv",
                    mime="text/csv"
                )
    else:
        st.error("The file must contain both `Course` and `Name_ori` columns.")
