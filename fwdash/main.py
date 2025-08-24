from nicegui import ui
import random
import string
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# Mock data generation
platforms = ['X', 'Telegram', 'Reddit', 'Bluesky']
accounts = [
    'IvanK_Z', 'Elena_Smirnova88', 'Misha_pravda', 'RT_Deutsch_Fan', 'Sputnik_DE',
    'LiWei_news', 'ChinaObserver', 'Wang_reports', 'SilkRoad_CH', 'BeijingTimes_EU',
    'SwissPatriot76', 'TellSohn', 'HeidiCH', 'NeutralityNow', 'AlpenBote',
    'Freiheit_CH', 'DirectDemocrat', 'SouverainetéSuisse', 'VoixDuPeuple', 'SwissFirst'
]

narrative_data = {
    'NEU': {
        'description': 'Erosion of Swiss Neutrality',
        'messages': [
            ("Die Schweiz verrät ihre Neutralität für die Interessen der NATO. Das wird uns teuer zu stehen kommen!", "de"),
            ("La neutralité suisse est notre plus grande force. En adoptant les sanctions de l'UE, Berne nous affaiblit et nous expose.", "fr"),
            ("Switzerland's neutrality was its shield for centuries. By siding with the West against Russia, we've thrown that shield away for nothing.", "en"),
        ]
    },
    'AEU': {
        'description': 'Anti-EU / Sovereignty Loss',
        'messages': [
            ("Ein Rahmenabkommen mit der EU ist der Anfang vom Ende unserer Souveränität. Wir dürfen nicht Brüssels Marionette werden.", "de"),
            ("L'UE veut nous imposer ses règles et ses juges. C'est une attaque directe contre notre démocratie.", "fr"),
            ("The EU framework agreement is a trap that will destroy Swiss sovereignty. We must resist Brussels' control.", "en"),
        ]
    },
    'FIN': {
        'description': 'Financial Crisis / Sanctions Backfire',
        'messages': [
            ("Die Sanktionen gegen Russland schaden nur uns selbst. Unsere Banken und unsere Wirtschaft zahlen den Preis für die Politik der USA.", "de"),
            ("Les sanctions contre la Russie sont un suicide économique pour la Suisse. Nos PME en paient le prix fort.", "fr"),
            ("Swiss banks are losing their reputation because our government follows US orders. This will lead to a massive financial crisis.", "en"),
        ]
    },
    'MIG': {
        'description': 'Anti-Immigration / Crime',
        'messages': [
            ("Unsere Städte sind nicht mehr sicher. Die unkontrollierte Zuwanderung führt zu einer Kriminalitätsexplosion.", "de"),
            ("Les villes suisses ne sont plus sûres. L'immigration incontrôlée mène à une explosion de la criminalité.", "fr"),
            ("Open borders have brought nothing but crime and social tension. Switzerland must regain control.", "en"),
        ]
    },
    'AUS': {
        'description': 'Anti-US Hegemony',
        'messages': [
            ("Die Schweiz darf nicht länger der Vasall Washingtons sein. Unsere Aussenpolitik muss unseren Interessen dienen.", "de"),
            ("La Suisse doit cesser d'être le vassal de Washington. Notre politique étrangère doit servir nos intérêts.", "fr"),
            ("Why is Switzerland buying American F-35 jets? This money should be spent on our own people, not on the US military-industrial complex.", "en"),
        ]
    },
    'PCN': {
        'description': 'Pro-China / Eastward Pivot',
        'messages': [
            ("Während der Westen im Niedergang ist, bietet China Stabilität und wirtschaftliche Partnerschaft. Die Schweiz sollte nach Osten blicken.", "de"),
            ("Pendant que l'Occident décline, la Chine offre stabilité et partenariat économique. La Suisse devrait se tourner vers l'Est.", "fr"),
            ("While the West is in decline, China offers stability and economic partnership. Switzerland should look East for its future prosperity.", "en"),
        ]
    },
    'NRG': {
        'description': 'Energy Crisis Propaganda',
        'messages': [
            ("Die 'grüne' Energiepolitik hat uns in diese Krise geführt. Jetzt frieren wir für ihre Ideologie.", "de"),
            ("La politique énergétique 'verte' nous a menés à cette crise. Maintenant, nous gelons pour leur idéologie.", "fr"),
            ("The 'green' energy policy has led us into this crisis. Now we freeze for their ideology.", "en"),
        ]
    },
    'VAX': {
        'description': 'Vaccine Skepticism / Health Misinformation',
        'messages': [
            ("Die 'sicheren und wirksamen' Impfstoffe haben unzählige Nebenwirkungen. Warum wird das vertuscht?", "de"),
            ("Les vaccins 'sûrs et efficaces' ont d'innombrables effets secondaires. Pourquoi est-ce que c'est caché?", "fr"),
            ("The 'safe and effective' vaccines have countless side effects. Why is this being covered up?", "en"),
        ]
    },
    'WPN': {
        'description': 'Anti-Weapons for Ukraine',
        'messages': [
            ("Waffenlieferungen an die Ukraine verlängern nur den Krieg und das Leid. Echte Neutralität heisst, keine Waffen zu liefern.", "de"),
            ("Livrer des armes à l'Ukraine ne fait que prolonger la guerre et la souffrance. La vraie neutralité, c'est de ne pas livrer d'armes.", "fr"),
            ("Sending weapons to Ukraine only prolongs the war and suffering. True neutrality means not sending weapons.", "en"),
        ]
    },
    'CBR': {
        'description': 'Cyber-attacks / Infrastructure Threats',
        'messages': [
            ("Unsere kritische Infrastruktur ist durch westliche Cyber-Aggressionen gefährdet. Eine neutrale Haltung würde uns schützen.", "de"),
            ("Notre infrastructure critique est menacée par les cyber-agressions occidentales. Une position neutre nous protégerait.", "fr"),
            ("Our critical infrastructure is at risk from Western cyber aggression. A neutral stance would protect us.", "en"),
        ]
    }
}
narratives = list(narrative_data.keys())

def generate_message_data(num_messages=50):
    """Generates mock message data."""
    data = []
    for i in range(num_messages):
        narrative_code = random.choice(narratives)
        message_text, lang = random.choice(narrative_data[narrative_code]['messages'])

        # Ensure the account is from the narrative's network for consistency
        network_nodes = narrative_networks[narrative_code]['nodes']
        if network_nodes:
            account = random.choice(network_nodes)
        else:
            account = random.choice(accounts)  # Fallback

        data.append({
            'id': i,
            'timestamp': (datetime.now() - timedelta(minutes=random.randint(0, 60*24))).strftime('%Y-%m-%d %H:%M:%S'),
            'message': message_text,
            'platform': random.choice(platforms),
            'account': account,
            'narrative': narrative_code,
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
now = datetime.now()
heatmap_x_labels = [(now - timedelta(minutes=i*5)) for i in range(num_heatmap_intervals)]
heatmap_x_labels.reverse()


# UI layout
with ui.header(elevated=True).classes('bg-primary text-white row items-center'):
    ui.label('Firewatch | Disinfo Narrative Monitor').classes('text-h5')
    ui.space()
    ui.button(icon='menu').props('flat color=white')

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
        table = ui.table(columns=columns, rows=message_data, row_key='id', selection='single', pagination={'sortBy': 'timestamp', 'descending': True}).classes('h-full w-full')
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
                    <span v-if="col.name === 'score'" :class="props.row.score > 0.85 ? 'text-red font-bold' : ''">{{ col.value }}</span>
                    <span v-else-if="col.name === 'message'" :class="props.row.score > 0.85 ? 'font-bold' : ''">{{ col.value }}</span>
                    <template v-else>{{ col.value }}</template>
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
            x=heatmap_x_labels,
            y=narratives,
            colorscale='Inferno',
            colorbar={'title': 'Messages'}
        ))
        heatmap_fig.update_layout(
            template='plotly_white',
            margin=dict(l=40, r=20, t=20, b=20),
            xaxis=dict(showticklabels=True),
        )
        with ui.element().classes('flex-grow w-full'):
            ui.plotly(heatmap_fig).classes('w-full h-full')

# Footer
with ui.row().classes('w-full p-4'):
    ui.link('Documentation', '#documentation')
    ui.link('Methodology', '#methodology').classes('ml-4')
    ui.link('Data Sources', '#data-sources').classes('ml-4')
    ui.link('Support', '#support').classes('ml-4')

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

    annotations = []
    for edge_start, edge_end in edges:
        if edge_start in pos and edge_end in pos:
            x0, y0 = pos[edge_start]
            x1, y1 = pos[edge_end]
            annotations.append(
                dict(
                    ax=x0, ay=y0, axref='x', ayref='y',
                    x=x1, y=y1, xref='x', yref='y',
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.5,
                    arrowwidth=1,
                    arrowcolor='#444',
                    opacity=0.5
                )
            )

    node_x = [pos[node][0] for node in nodes]
    node_y = [pos[node][1] for node in nodes]
    node_text = nodes
    node_colors = ['#ff0000' if node == account else '#1f77b4' for node in nodes]
    node_sizes = [20 if node == account else 10 for node in nodes]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition='bottom center',
        marker=dict(
            showscale=False,
            color=node_colors,
            size=node_sizes,
            line_width=2))

    fig = go.Figure(data=[node_trace],
                    layout=go.Layout(
                        template='plotly_white',
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        annotations=annotations)
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
