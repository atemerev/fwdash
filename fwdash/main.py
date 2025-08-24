from nicegui import ui
import random
import string
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# Mock data generation
platforms = ['X', 'Telegram', 'Reddit', 'Bluesky']
narratives = ['Naz', 'Bio', 'Con', 'Rcp', 'Ele', 'War', 'Eco', 'Imm', 'Pol', 'Fin']
accounts = [f'user_{"".join(random.choices(string.ascii_lowercase + string.digits, k=6))}' for _ in range(50)]

def generate_message_data(num_messages=50):
    """Generates mock message data."""
    data = []
    for i in range(num_messages):
        narrative = random.choice(narratives)
        # Ensure the account is from the narrative's network for consistency
        network_nodes = narrative_networks[narrative]['nodes']
        if network_nodes:
            account = random.choice(network_nodes)
        else:
            account = random.choice(accounts)  # Fallback

        data.append({
            'id': i,
            'timestamp': (datetime.now() - timedelta(minutes=random.randint(0, 60*24))).strftime('%Y-%m-%d %H:%M:%S'),
            'message': f'This is a sample message for narrative {narrative}. ' + ''.join(random.choices(string.ascii_letters + ' ', k=80)),
            'platform': random.choice(platforms),
            'account': account,
            'narrative': narrative,
            'score': round(random.uniform(0.5, 1.0), 2)
        })
    return data

# Mock data for networks and heatmap
narrative_networks = {}
for narrative in narratives:
    num_nodes = random.randint(5, 15)
    # Ensure the accounts in the network are from the main accounts list
    if len(accounts) >= num_nodes:
        narrative_accounts = random.sample(accounts, num_nodes)
    else:
        narrative_accounts = accounts
    
    edges = []
    for i in range(len(narrative_accounts)):
        for j in range(i + 1, len(narrative_accounts)):
            if random.random() < 0.3:
                edges.append((narrative_accounts[i], narrative_accounts[j]))
    narrative_networks[narrative] = {'nodes': narrative_accounts, 'edges': edges}

message_data = generate_message_data()

# Heatmap data
num_heatmap_intervals = 200
heatmap_data = np.random.gamma(2.0, 2.0, size=(len(narratives), num_heatmap_intervals))


# UI layout
with ui.header(elevated=True).classes('bg-primary text-white'):
    ui.label('Firewatch | Disinfo Narrative Monitor').classes('text-h5')

# Top panel: Messages Table
with ui.row().classes('w-full'):
    with ui.card().classes('w-full h-96 overflow-y-auto'):
        ui.label('Detected Propaganda Activity').classes('text-h6')
        columns = [
            {'name': 'id', 'label': 'ID', 'field': 'id', 'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'timestamp', 'label': 'Timestamp', 'field': 'timestamp', 'sortable': True},
            {'name': 'message', 'label': 'Message', 'field': 'message', 'align': 'left', 'style': 'white-space: normal;'},
            {'name': 'platform', 'label': 'Platform', 'field': 'platform', 'sortable': True},
            {'name': 'account', 'label': 'Account', 'field': 'account', 'sortable': True},
            {'name': 'narrative', 'label': 'Narrative', 'field': 'narrative', 'sortable': True},
            {'name': 'score', 'label': 'Score', 'field': 'score', 'sortable': True},
        ]
        table = ui.table(columns=columns, rows=message_data, row_key='id', selection='single').classes('h-full')
        table.add_slot('header', r'''
            <q-tr :props="props">
                <q-th v-for="col in props.cols" :key="col.name" :props="props" :class="col.headerClasses">
                    {{ col.label }}
                </q-th>
            </q-tr>
        ''')
        table.add_slot('body', r'''
            <q-tr :props="props" @click="$parent.$emit('row-click', props.row)" class="cursor-pointer">
                <q-td v-for="col in props.cols" :key="col.name" :props="props" :class="col.classes" :style="col.style">
                    {{ col.value }}
                </q-td>
            </q-tr>
        ''')


# Bottom panels
with ui.row().classes('w-full no-wrap'):
    # Panel 2: Network Graph
    with ui.card().classes('w-1/2 h-96 flex flex-col'):
        ui.label('Account Network').classes('text-h6')
        
        fig = go.Figure()
        fig.update_layout(
            template='plotly_white',
            xaxis={'showgrid': False, 'zeroline': False, 'visible': False},
            yaxis={'showgrid': False, 'zeroline': False, 'visible': False},
            annotations=[{
                'text': 'Select a message to see the network',
                'xref': 'paper', 'yref': 'paper',
                'showarrow': False, 'font': {'size': 16}
            }]
        )
        with ui.element().classes('flex-grow w-full'):
            network_plot = ui.plotly(fig).classes('w-full h-full')

    # Panel 3: Narrative Density Heatmap
    with ui.card().classes('w-1/2 h-96 flex flex-col'):
        ui.label('Narrative Density Heatmap').classes('text-h6')

        heatmap_fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=list(range(num_heatmap_intervals)),
            y=narratives,
            colorscale='Inferno',
            colorbar={'title': 'Messages'}
        ))
        heatmap_fig.update_layout(
            template='plotly_white',
            margin=dict(l=40, r=20, t=20, b=20),
            xaxis=dict(showticklabels=False),
        )
        with ui.element().classes('flex-grow w-full'):
            ui.plotly(heatmap_fig).classes('w-full h-full')

# Interactivity
def update_network_graph(selected_rows, plot):
    """Updates the network graph based on table selection."""
    if not selected_rows:
        # On clear selection, revert to initial message
        fig = go.Figure()
        fig.update_layout(
            template='plotly_white',
            xaxis={'showgrid': False, 'zeroline': False, 'visible': False},
            yaxis={'showgrid': False, 'zeroline': False, 'visible': False},
            annotations=[{
                'text': 'Select a message to see the network',
                'xref': 'paper', 'yref': 'paper',
                'showarrow': False, 'font': {'size': 16}
            }]
        )
        plot.figure = fig
        plot.update()
        return

    selected_row = selected_rows[0]
    account = selected_row['account']
    narrative = selected_row['narrative']
    
    network_data = narrative_networks[narrative]
    nodes = network_data['nodes']
    edges = network_data['edges']

    # Create node positions for visualization
    pos = {node: (random.random(), random.random()) for node in nodes}

    edge_x = []
    edge_y = []
    for edge_start, edge_end in edges:
        if edge_start in pos and edge_end in pos:
            x0, y0 = pos[edge_start]
            x1, y1 = pos[edge_end]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#444'),
        hoverinfo='none',
        mode='lines')

    node_x = [pos[node][0] for node in nodes]
    node_y = [pos[node][1] for node in nodes]
    node_text = nodes
    node_colors = ['#ff0000' if node == account else '#1f77b4' for node in nodes]
    node_sizes = [20 if node == account else 10 for node in nodes]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color=node_colors,
            size=node_sizes,
            line_width=2))

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=f'Network for Narrative: {narrative}',
                        template='plotly_white',
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    plot.figure = fig
    plot.update()

def handle_row_click(e):
    """Handle custom row-click event."""
    clicked_row = e.args
    if not clicked_row:
        return

    # Toggle selection
    if table.selected and table.selected[0]['id'] == clicked_row['id']:
        table.selected.clear()
    else:
        table.selected.clear()
        table.selected.append(clicked_row)

    # Update the network graph
    update_network_graph(table.selected, network_plot)

table.on('row-click', handle_row_click)

ui.run()
