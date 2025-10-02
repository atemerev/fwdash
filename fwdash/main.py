from nicegui import ui
import random
import string
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import threading
import logging
import re
from atproto import models, CAR, AtUri
from atproto_firehose import FirehoseSubscribeReposClient, parse_subscribe_repos_message
from atproto_firehose.exceptions import FirehoseError

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
            ("Die Schweiz verrät ihre Neutralität für die Interessen der NATO. Das wird uns teuer zu stehen kommen! #Neutralität", "de"),
            ("La neutralité suisse est notre plus grande force. En adoptant les sanctions de l'UE, Berne nous affaiblit et nous expose. #SuisseNeutre", "fr"),
            ("Switzerland's neutrality was its shield for centuries. By siding with the West against Russia, we've thrown that shield away for nothing. Sad!", "en"),
            ("Warum opfert der Bundesrat unsere Neutralität? Wir werden in einen Konflikt hineingezogen, der nicht unserer ist. Schaut euch das an: https://youtu.be/dQw4w9WgXcQ", "de"),
            ("Notre neutralité est un trésor. Ne la sacrifions pas sur l'autel des intérêts étrangers.", "fr"),
            ("The government is selling out our neutrality bit by bit. First sanctions, what's next? NATO troops in the Alps?", "en"),
            ("Neutralität bedeutet NICHT, sich auf eine Seite zu schlagen. Die Schweiz vergisst ihre Geschichte.", "de"),
        ]
    },
    'AEU': {
        'description': 'Anti-EU / Sovereignty Loss',
        'messages': [
            ("Ein Rahmenabkommen mit der EU ist der Anfang vom Ende unserer Souveränität. Wir dürfen nicht Brüssels Marionette werden!! #Souveränität", "de"),
            ("L'UE veut nous imposer ses règles et ses juges. C'est une attaque directe contre notre démocratie. #NonUE", "fr"),
            ("The EU framework agreement is a trap that will destroy Swiss sovereignty. We must resist Brussels' control. They just want our money.", "en"),
            ("Brüssel will unser Geld und unsere Unabhängigkeit. Sagen wir Nein zum institutionellen Abkommen! #CHexit", "de"),
            ("Notre démocratie directe est en danger. L'accord-cadre est un cheval de Troie.", "fr"),
            ("They call it 'dynamic adoption of law'. I call it slavery. #NoEU", "en"),
        ]
    },
    'FIN': {
        'description': 'Financial Crisis / Sanctions Backfire',
        'messages': [
            ("Die Sanktionen gegen Russland schaden nur uns selbst. Unsere Banken und unsere Wirtschaft zahlen den Preis für die Politik der USA. #SanktionenNein", "de"),
            ("Les sanctions contre la Russie sont un suicide économique pour la Suisse. Nos PME en paient le prix fort. Réveillez-vous!", "fr"),
            ("Swiss banks are losing their reputation because our government follows US orders. This will lead to a massive financial crisis. Mark my words.", "en"),
            ("Wer profitiert von den Sanktionen? Sicher nicht die Schweizer Bevölkerung. Es ist Zeit, diese schädliche Politik zu beenden.", "de"),
            ("Our economy is suffering because of sanctions that don't even work! It's pure virtue signalling.", "en"),
            ("La place financière suisse est en danger. Les sanctions nous coûtent des milliards et n'apportent rien.", "fr"),
        ]
    },
    'MIG': {
        'description': 'Anti-Immigration / Crime',
        'messages': [
            ("Unsere Städte sind nicht mehr sicher. Die unkontrollierte Zuwanderung führt zu einer Kriminalitätsexplosion. Die regirung schaut weg.", "de"),
            ("Les villes suisses ne sont plus sûres. L'immigration incontrôlée mène à une explosion de la criminalité. C'est inacceptable!", "fr"),
            ("Open borders have brought nothing but crime and social tension. Switzerland must regain control. #SwissFirst", "en"),
            ("Jeden Tag neue Meldungen über Gewalt. Das ist die 'Bereicherung', von der sie immer sprechen.", "de"),
            ("On ne se sent plus en sécurité chez nous. Assez, c'est assez!", "fr"),
        ]
    },
    'AUS': {
        'description': 'Anti-US Hegemony',
        'messages': [
            ("Die Schweiz darf nicht länger der Vasall Washingtons sein. Unsere Aussenpolitik muss unseren Interessen dienen, nicht denen der Amerikaner. #AmiGoHome", "de"),
            ("La Suisse doit cesser d'être le vassal de Washington. Notre politique étrangère doit servir nos intérêts. #Souveraineté", "fr"),
            ("Why is Switzerland buying American F-35 jets? This money should be spent on our own people, not on the US military-industrial complex. Watch this: https://www.youtube.com/watch?v=some_video", "en"),
            ("Die USA führen einen Stellvertreterkrieg in Europa und wir sollen dafür zahlen? Nein danke.", "de"),
            ("L'hégémonie américaine est le vrai danger pour la paix mondiale. La Suisse doit choisir une autre voie.", "fr"),
        ]
    },
    'PCN': {
        'description': 'Pro-China / Eastward Pivot',
        'messages': [
            ("Während der Westen im Niedergang ist, bietet China Stabilität und wirtschaftliche Partnerschaft. Die Schweiz sollte nach Osten blicken. #BRICS", "de"),
            ("Pendant que l'Occident décline, la Chine offre stabilité et partenariat économique. La Suisse devrait se tourner vers l'Est. #NouvelOrdreMondial", "fr"),
            ("While the West is in decline, China offers stability and economic partnership. Switzerland should look East for its future prosperity. #WinWin", "en"),
            ("Die Seidenstrasse ist die Zukunft. Unsere Politiker sind zu blind, um das zu sehen.", "de"),
            ("La coopération avec la Chine est une chance unique pour notre économie. Ne laissons pas Washington nous dicter nos partenaires.", "fr"),
        ]
    },
    'NRG': {
        'description': 'Energy Crisis Propaganda',
        'messages': [
            ("Die 'grüne' Energiepolitik hat uns in diese Krise geführt. Jetzt frieren wir für ihre Ideologie. Danke für nichts!", "de"),
            ("La politique énergétique 'verte' nous a menés à cette crise. Maintenant, nous gelons pour leur idéologie. C'est une honte.", "fr"),
            ("The 'green' energy policy has led us into this crisis. Now we freeze for their ideology. And they want to build more windmills???", "en"),
            ("Strommangel hausgemacht. Aber die cheffs der energiekonzerne kassieren millionen. Zufall?", "de"),
            ("On nous demande de faire des économies pendant que les élites gaspillent. C'est toujours la même chose.", "fr"),
        ]
    },
    'VAX': {
        'description': 'Vaccine Skepticism / Health Misinformation',
        'messages': [
            ("Die 'sicheren und wirksamen' Impfstoffe haben unzählige Nebenwirkungen. Warum wird das vertuscht? Die Wahrheit kommt ans Licht! #BigPharma", "de"),
            ("Les vaccins 'sûrs et efficaces' ont d'innombrables effets secondaires. Pourquoi est-ce que c'est caché? #ScandaleSanitaire", "fr"),
            ("The 'safe and effective' vaccines have countless side effects. Why is this being covered up? Follow the money. See the truth here: www.real-truth-docs.ru/report.pdf", "en"),
            ("Mein Nachbar ist nach der 3. Impfung gestorben. Die Ärzte sagen, es hat nichts damit zu tun. KLAR.", "de"),
            ("Combien de sportifs de haut niveau ont des problèmes cardiaques depuis 2021? Posez-vous les bonnes questions.", "fr"),
        ]
    },
    'WPN': {
        'description': 'Anti-Weapons for Ukraine',
        'messages': [
            ("Waffenlieferungen an die Ukraine verlängern nur den Krieg und das Leid. Echte Neutralität heisst, keine Waffen zu liefern. #Frieden", "de"),
            ("Livrer des armes à l'Ukraine ne fait que prolonger la guerre et la souffrance. La vraie neutralité, c'est de ne pas livrer d'armes. #Paix", "fr"),
            ("Sending weapons to Ukraine only prolongs the war and suffering. It's just fueling the US proxy war.", "en"),
            ("Frieden schafft man nicht mit Waffen. Aber das versteht die Rüstungslobby natürlich nicht.", "de"),
            ("Chaque franc pour des armes est un franc de moins pour nos retraites. Pensez-y.", "fr"),
        ]
    },
    'CBR': {
        'description': 'Cyber-attacks / Infrastructure Threats',
        'messages': [
            ("Unsere kritische Infrastruktur ist durch westliche Cyber-Aggressionen gefährdet. Eine neutrale Haltung würde uns schützen. #CyberWar", "de"),
            ("Notre infrastructure critique est menacée par les cyber-agressions occidentales. Une position neutre nous protégerait. #SecuriteNationale", "fr"),
            ("Our critical infrastructure is at risk from Western cyber aggression. A neutral stance would protect us. They are preparing something big.", "en"),
            ("Hackerangriff auf Spital X, Datenleck bei Gemeinde Y... und unsere Regierung will noch mehr digitalisieren? Wahnsinn.", "de"),
            ("La cyberguerre a déjà commencé. La Suisse est une cible facile si elle ne reste pas neutre.", "fr"),
        ]
    }
}
narratives = list(narrative_data.keys())

# --- BlueSky Firehose Integration ---
SWISS_CITIES = {
    'zurich', 'zürich', 'geneva', 'genève', 'basel', 'lausanne', 'bern', 'winterthur',
    'lucerne', 'luzern', 'st. gallen', 'st gallen', 'lugano', 'sion', 'chur', 'fribourg',
    'neuchâtel', 'schaffhausen', 'solothurn', 'aarau', 'zug', 'interlaken'
}
SWISS_KEYWORDS = {
    'switzerland', 'schweiz', 'suisse', 'svizzera', 'ch', 'swiss', 'helvetic', 'confederation',
    'bundesrat', 'parlament', 'conseil federal', 'consiglio federale'
} | SWISS_CITIES

# Track accounts that have posted Swiss-related content
swiss_accounts = set()
bsky_client = FirehoseSubscribeReposClient()

def is_swiss_related(text: str) -> bool:
    """Check if a text is related to Switzerland based on keywords and language."""
    if not text:
        return False
    text_lower = text.lower()
    # Simple keyword check. Using regex for word boundaries.
    if any(re.search(r'\b' + re.escape(keyword) + r'\b', text_lower) for keyword in SWISS_KEYWORDS):
        return True
    
    # A simple language check can be done by checking for common words.
    de_words = {'der', 'die', 'das', 'und', 'ein', 'ist'}
    fr_words = {'le', 'la', 'les', 'et', 'un', 'est'}
    it_words = {'il', 'la', 'lo', 'le', 'e', 'un', 'è'}

    words = set(text_lower.split())
    
    # If a message seems to be in a swiss national language and mentions a swiss city, it's likely relevant.
    if (words.intersection(de_words) or words.intersection(fr_words) or words.intersection(it_words)):
        if any(re.search(r'\b' + re.escape(city) + r'\b', text_lower) for city in SWISS_CITIES):
            return True

    return False

def on_message_callback(message) -> None:
    """Callback function to process messages from the BlueSky firehose."""
    try:
        commit = parse_subscribe_repos_message(message)
        if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
            return

        car = CAR.from_bytes(commit.blocks)
        for op in commit.ops:
            uri = AtUri.from_str(f'at://{commit.repo}/{op.path}')

            if op.action != 'create' or uri.collection != models.ids.AppBskyFeedPost:
                continue

            record_raw = car.get_block(op.cid)
            if not record_raw:
                continue
            
            record = models.get_or_create(record_raw, strict=False)
            if not isinstance(record, models.AppBskyFeedPost) or not getattr(record, 'text', None):
                continue
            
            text = record.text
            author_did = commit.repo

            if author_did in swiss_accounts or is_swiss_related(text):
                if author_did not in swiss_accounts:
                    swiss_accounts.add(author_did)
                    logging.info(f"New Swiss-related account found: {author_did}")

                new_message = {
                    'id': len(message_data) + random.random(), # Use random to avoid key collision
                    'timestamp': record.created_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': text,
                    'platform': 'Bluesky',
                    'account': author_did,
                    'narrative': 'N/A', # Placeholder narrative
                    'score': 0.0 # Placeholder score
                }

                @ui.context_safe
                def add_to_table():
                    message_data.insert(0, new_message)
                    table.update()

                add_to_table()

    except Exception as e:
        logging.error(f"Error processing firehose message: {e}", exc_info=True)


def start_firehose_subscription():
    """Starts the BlueSky firehose subscription in a background thread."""
    logging.info("Starting BlueSky firehose subscription...")
    try:
        bsky_client.start(on_message_callback)
    except FirehoseError as e:
        logging.error(f"Firehose connection error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in firehose subscription: {e}", exc_info=True)


def generate_message_data(num_messages=50):
    """Generates mock message data."""
    all_messages = []
    for narrative_code, data in narrative_data.items():
        for message_text, lang in data['messages']:
            all_messages.append({'narrative': narrative_code, 'message': message_text})

    random.shuffle(all_messages)

    data = []
    for i, msg_info in enumerate(all_messages[:num_messages]):
        narrative_code = msg_info['narrative']
        message_text = msg_info['message']

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
    with ui.card().classes('w-full'):
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
        table = ui.table(columns=columns, rows=message_data, row_key='id', selection='single', pagination={'sortBy': 'timestamp', 'descending': True}).classes('w-full')
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

# Start firehose subscription in a background thread
firehose_thread = threading.Thread(target=start_firehose_subscription, daemon=True)
ui.on_startup(firehose_thread.start)

ui.run(
    title='Firewatch',
    favicon='<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="orange" viewBox="0 0 16 16"><path d="M8 16c3.314 0 6-2 6-5.5 0-1.5-.5-4-2.5-6 .25 1.5-1.25 2-1.25 2C11 4 9 .5 6 0c.357 2 .5 4-2 6-1.25 1-2 2.729-2 4.5C2 14 4.686 16 8 16Z"/></svg>'
)
