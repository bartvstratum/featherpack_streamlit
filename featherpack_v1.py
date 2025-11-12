import pandas as pd
import streamlit as st
import glob
from datetime import datetime
import plotly.express as px


def create_empty_df():
    columns = ['name', 'desc', 'category', 'weight', 'qty', 'wearable', 'consumable', 'luxury']
    return pd.DataFrame(columns=columns)


def handle_config_selection():
    """
    Handle config/CSV selection and creation.
    """
    
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

    selected_config = st.selectbox('Available configs:', csv_files, index=index)
    return selected_config


def display_summary(combined_df, category_weights):
    """
    Display weight summary metrics and charts
    """

    total_weight = combined_df['total_weight'].sum()
    wearable_weight = combined_df[combined_df['wearable'] == True]['total_weight'].sum()
    consumable_weight = combined_df[combined_df['consumable'] == True]['total_weight'].sum()
    luxury_weight = combined_df[combined_df['luxury'] == True]['total_weight'].sum()
    base_weight = total_weight - wearable_weight - consumable_weight

    col_left, col_right = st.columns([1, 3])

    with col_left:
        st.metric('Total Weight', f'{total_weight:.0f}')
        st.metric('Base Weight', f'{base_weight:.0f}')
        st.metric('👕 Wearable', f'{wearable_weight:.0f}')
        st.metric('🍞 Consumable', f'{consumable_weight:.0f}')
        st.metric('📸 Luxury', f'{luxury_weight:.0f}')

    with col_right:
        fig_pie = px.pie(
            category_weights,
            values='total_weight',
            names='category',
            title='Weight by Category',
            hover_data=['total_weight'],
            hole=0.4
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}<br>Weight: %{value:.2f}<br>Percent: %{percent}'
        )
        st.plotly_chart(fig_pie, use_container_width=True)


def display_add_category_buttons(df, selected_config):
    """
    Display add category and save changes buttons
    """

    def on_add_category():
        new_cat = st.session_state.new_category.strip()
        if new_cat:
            new_row = pd.DataFrame({
                'name': [''],
                'desc': [''],
                'category': [new_cat],
                'weight': [0],
                'qty': [1],
                'wearable': [False],
                'consumable': [False],
                'luxury': [False]
            })
            df_updated = pd.concat([df, new_row], ignore_index=True)
            df_updated.to_csv(selected_config, index=False)
            st.session_state.new_category = ''

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.text_input('New category', key='new_category', label_visibility='collapsed', placeholder='Add new category')
    with col2:
        st.button('Add Category', on_click=on_add_category, key='add_cat_top')
    with col3:
        st.button('Save Changes', key='save_top')


def display_category_editor(category, df, selected_config):
    """
    Display editor for a single category with delete button
    """

    col1, col2 = st.columns([12, 1])
    with col1:
        st.subheader(category.title())
    with col2:
        st.markdown(f"""
            <style>
            button[data-testid="baseButton-secondary"]{{
                font-size: 10px;
                padding: 2px 8px;
            }}
            </style>
        """, unsafe_allow_html=True)
        if st.button('🗑️', key=f'delete_{category}', help='Delete category'):
            st.session_state[f'confirm_delete_{category}'] = True

    # Confirmation dialog
    if st.session_state.get(f'confirm_delete_{category}'):
        st.warning(f'Delete category "{category}"? This will remove all items in this category.')
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            if st.button('Yes', key=f'confirm_yes_{category}'):
                df_updated = df[df['category'] != category]
                df_updated.to_csv(selected_config, index=False)
                del st.session_state[f'confirm_delete_{category}']
                st.rerun()
        with col2:
            if st.button('No', key=f'confirm_no_{category}'):
                del st.session_state[f'confirm_delete_{category}']
                st.rerun()

    category_df = df[df['category'] == category].drop(columns=['category']).reset_index(drop=True)
    category_df = category_df.rename(columns={'wearable': '👕', 'consumable': '🍞', 'luxury': '📸', 'qty': '#', 'weight': '⚖️'})
    category_df = category_df[['name', 'desc', '#', '👕', '🍞', '📸', '⚖️']]

    edited_df = st.data_editor(
        category_df,
        key=f"editor_{category}",
        hide_index=True,
        num_rows='dynamic',
        column_config={
            'desc': st.column_config.TextColumn(width=200),
            '⚖️': st.column_config.NumberColumn(width=20, default=0, help="Weight"),
            '#': st.column_config.NumberColumn(width=10, default=1),
            '👕': st.column_config.CheckboxColumn(width=20, default=False),
            '🍞': st.column_config.CheckboxColumn(width=20, default=False),
            '📸': st.column_config.CheckboxColumn(width=20, default=False),
        }
    )

    # Rename columns back and add category
    edited_df = edited_df.rename(columns={'👕': 'wearable', '🍞': 'consumable', '📸': 'luxury', '#': 'qty', '⚖️': 'weight'})
    edited_df['category'] = category
    return edited_df


def main():
    st.title('FeatherPack 🪶')

    selected_config = handle_config_selection()

    if selected_config:
        df = pd.read_csv(selected_config)
        categories = df['category'].dropna().unique()

        # First pass: collect data for summary
        edited_dfs = []
        for category in categories:
            category_df = df[df['category'] == category].drop(columns=['category']).reset_index(drop=True)
            category_df = category_df.rename(columns={'wearable': '👕', 'consumable': '🍞', 'luxury': '📸', 'qty': '#', 'weight': '⚖️'})
            category_df = category_df[['name', 'desc', '#', '👕', '🍞', '📸', '⚖️']]
            temp_df = category_df.rename(columns={'👕': 'wearable', '🍞': 'consumable', '📸': 'luxury', '#': 'qty', '⚖️': 'weight'})
            temp_df['category'] = category
            edited_dfs.append(temp_df)

        # Display summary
        if edited_dfs:
            combined_df = pd.concat(edited_dfs, ignore_index=True)
            combined_df['total_weight'] = combined_df['qty'] * combined_df['weight']
            category_weights = combined_df.groupby('category')['total_weight'].sum().reset_index()
            category_weights = category_weights.sort_values('total_weight', ascending=False)
            display_summary(combined_df, category_weights)

        # Add category and save buttons
        display_add_category_buttons(df, selected_config)

        # Second pass: display category editors
        edited_dfs = []
        for category in categories:
            edited_df = display_category_editor(category, df, selected_config)
            edited_dfs.append(edited_df)

        # Handle saving
        if edited_dfs:
            combined_df = pd.concat(edited_dfs, ignore_index=True)
            if st.session_state.get('save_top'):
                combined_df_save = combined_df[['name', 'desc', 'category', 'weight', 'qty', 'wearable', 'consumable', 'luxury']]
                combined_df_save.to_csv(selected_config, index=False)
                st.session_state.last_saved = datetime.now()
                st.rerun()

            if 'last_saved' in st.session_state:
                st.success(f'Saved ({st.session_state.last_saved})')


if __name__ == '__main__':
    main()
