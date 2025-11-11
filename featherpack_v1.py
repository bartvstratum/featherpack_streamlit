import pandas as pd
import streamlit as st
import glob


def create_empty_df():
    columns = ['name', 'desc', 'category', 'weight', 'qty', 'wearable', 'consumable', 'luxury']
    return pd.DataFrame(columns=columns)


def main():
    #st.set_page_config(layout='wide')
    st.title('FeatherPack 🪶')

    # Get available configs.
    csv_files = sorted(glob.glob('*.csv'))

    def on_create_new_config():
        name = st.session_state.new_config.strip()
        if name:
            if not name.endswith('.csv'):
                name += '.csv'
            df = create_empty_df()
            df.to_csv(name, index=False)
            st.session_state.newly_created_config = name
            st.session_state.new_config = ''

    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input('New config', key='new_config', label_visibility='collapsed', placeholder='Create new empty config')
    with col2:
        st.button('Create', on_click=on_create_new_config)

    # Determine the index for the selectbox
    if 'newly_created_config' in st.session_state and st.session_state.newly_created_config in csv_files:
        index = csv_files.index(st.session_state.newly_created_config)
        del st.session_state.newly_created_config
    elif len(csv_files) == 1:
        index = 0
    else:
        index = None

    selected_config = st.selectbox(
            'Available configs:', csv_files, index=index)

    if selected_config:
      df = pd.read_csv(selected_config)

      # Get unique categories
      categories = df['category'].dropna().unique()

      for category in categories:
          st.subheader(category.title())
          category_df = df[df['category'] == category].drop(columns=['category']).reset_index(drop=True)
          category_df = category_df.rename(columns={'wearable': '👕', 'consumable': '🍞', 'luxury': '📸', 'qty': '#', 'weight': '⚖️'})
          category_df = category_df[['name', 'desc', '#', '👕', '🍞', '📸', '⚖️']]
          st.data_editor(
              category_df,
              key=f"editor_{category}",
              hide_index=True,
              column_config={
                  'desc': st.column_config.TextColumn(width=200),
                  '⚖️': st.column_config.NumberColumn(width=20, help="Weight"),
                  '#': st.column_config.NumberColumn(width=10),
                  '👕': st.column_config.CheckboxColumn(width=20),
                  '🍞': st.column_config.CheckboxColumn(width=20),
                  '📸': st.column_config.CheckboxColumn(width=20),
              }
          )

if __name__ == '__main__':
    main()
