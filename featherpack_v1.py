import pandas as pd
import streamlit as st
import glob
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt


# Some global settings.
# Don't change these icons; it will break existing CSV files.
consumable_icon = '🍞'
wearable_icon = '🥾'
luxury_icon = '🎩'
weight_icon = '⚖️'


def create_empty_df():
    columns = ['name', 'desc', 'category', weight_icon, '#', wearable_icon, consumable_icon, luxury_icon]
    return pd.DataFrame(columns=columns)


def sort_by_weight(df):
    """
    Sort dataframe: categories by total weight (descending), items within each category by item weight (descending)
    """
    df['item_weight'] = df['#'] * df[weight_icon]
    category_totals = df.groupby('category')['item_weight'].sum().sort_values(ascending=False)
    df['category'] = pd.Categorical(df['category'], categories=category_totals.index, ordered=True)
    df = df.sort_values(['category', 'item_weight'], ascending=[True, False])
    df = df.drop(columns=['item_weight'])
    return df


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
    wearable_weight = combined_df[combined_df[wearable_icon] == True]['total_weight'].sum()
    consumable_weight = combined_df[combined_df[consumable_icon] == True]['total_weight'].sum()
    luxury_weight = combined_df[combined_df[luxury_icon] == True]['total_weight'].sum()
    base_weight = total_weight - wearable_weight - consumable_weight

    col_left, col_right = st.columns([1, 3])

    with col_left:
        st.metric('Total Weight', f'{total_weight:.0f}')
        st.metric('Base Weight', f'{base_weight:.0f}')
        st.metric(f'{wearable_icon} Wearable', f'{wearable_weight:.0f}')
        st.metric(f'{consumable_icon} Consumable', f'{consumable_weight:.0f}')
        st.metric(f'{luxury_icon} Luxury', f'{luxury_weight:.0f}')

    with col_right:
        category_weights['percentage'] = category_weights['total_weight'] / category_weights['total_weight'].sum()

        # Normalize percentages to 0-1 range (min category = 0/blue, max category = 1/red)
        pct_values = category_weights['percentage'].values
        normalized = (pct_values - pct_values.min()) / (pct_values.max() - pct_values.min())
        rgba_colors = plt.cm.RdBu_r(normalized)
        colors = [f'rgb({int(r*255)},{int(g*255)},{int(b*255)})' for r, g, b, _ in rgba_colors]

        fig_pie = go.Figure(data=[go.Pie(
            labels=category_weights['category'],
            values=category_weights['total_weight'],
            hole=0.4,
            marker=dict(colors=colors),
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}<br>Weight: %{value:.2f}<br>Percent: %{percent}<extra></extra>'
        )])
        fig_pie.update_layout(title='Weight by Category')
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
                weight_icon: [0],
                '#': [1],
                wearable_icon: [False],
                consumable_icon: [False],
                luxury_icon: [False]
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

    # Calculate category total weight
    category_df = df[df['category'] == category]
    total_weight = (category_df['#'] * category_df[weight_icon]).sum()

    col1, col2 = st.columns([12, 1])
    with col1:
        st.subheader(f"{category.title()} ({total_weight:.0f} g)")
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
    category_df = category_df[['name', 'desc', '#', wearable_icon, consumable_icon, luxury_icon, weight_icon]]

    edited_df = st.data_editor(
        category_df,
        key=f"editor_{category}",
        hide_index=True,
        num_rows='dynamic',
        column_config={
            'desc': st.column_config.TextColumn(width=200),
            weight_icon: st.column_config.NumberColumn(width=20, default=0, help="Weight"),
            '#': st.column_config.NumberColumn(width=10, default=1),
            wearable_icon: st.column_config.CheckboxColumn(width=20, default=False),
            consumable_icon: st.column_config.CheckboxColumn(width=20, default=False),
            luxury_icon: st.column_config.CheckboxColumn(width=20, default=False),
        }
    )

    # Add category back
    edited_df['category'] = category
    return edited_df


def main():

    st.title('FeatherPack 🪶')
    st.set_page_config(page_title='FeatherPack 🪶')

    # Get available configs (.csv) and select one.
    selected_config = handle_config_selection()

    if selected_config:
        # Read CSV with Pandas.
        df = pd.read_csv(selected_config)
        df = sort_by_weight(df)
        categories = df['category'].dropna().unique()

        # Display summary
        combined_df = df.copy()
        combined_df['total_weight'] = combined_df['#'] * combined_df[weight_icon]
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
                combined_df = sort_by_weight(combined_df)
                combined_df.to_csv(selected_config, index=False)
                st.session_state.last_saved = datetime.now()
                st.rerun()

            if 'last_saved' in st.session_state:
                st.success(f'Saved ({st.session_state.last_saved})')


if __name__ == '__main__':
    main()
