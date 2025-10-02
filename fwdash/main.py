from nicegui import ui
import random
import string
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import threading
import logging
import re
import queue
import requests
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
message_queue = queue.Queue()

# --- BlueSky Firehose Integration ---
SWISS_CITIES = {
    'zurich', 'zürich', 'geneva', 'genève', 'basel', 'lausanne', 'bern', 'winterthur',
    'lucerne', 'luzern', 'st. gallen', 'st gallen', 'lugano', 'sion', 'chur', 'fribourg',
    'neuchâtel', 'schaffhausen', 'solothurn', 'aarau', 'zug', 'interlaken', 'bellinzona',
    'Biel', 'Bienne', 'Thun', 'Köniz', 'La Chaux-de-Fonds', 'Uster', 'Rapperswil', 'Jona'
}

# High-confidence keywords that are very specific to Switzerland
HIGH_CONFIDENCE_SWISS_KEYWORDS = {
    'switzerland', 'schweiz', 'suisse', 'svizzera', 'helvetic', 'confederation', 'swiss', 'ch',
    'bundesrat', 'nationalrat', 'ständerat', 'volksinitiative', 'abstimmung', 'referendum',
    'conseil fédéral', 'conseil national', 'conseil des états', 'votation',
    'consiglio federale', 'consiglio nazionale', 'consiglio degli stati', 'votazione'
}

# Keywords that are often Swiss-related but require language context to avoid false positives
CONTEXTUAL_SWISS_KEYWORDS = SWISS_CITIES | {
    # Full canton names (ambiguous ones like 'zug', 'jura', 'uri' are excluded)
    'aargau', 'appenzell', 'basel-landschaft', 'basel-stadt', 'geneva', 'glarus',
    'graubünden', 'grisons', 'lucerne', 'neuchâtel', 'nidwalden', 'obwalden',
    'schaffhausen', 'schwyz', 'solothurn', 'st. gallen', 'thurgau', 'ticino',
    'vaud', 'valais', 'zürich',
    # Politics (less ambiguous terms, parties common in DE/FR are excluded)
    'parlament', 'parlement', 'parlamento',
    'svp', 'udc', 'plr', 'glp', 'pvl'
    # Ambiguous party names and canton abbreviations are excluded
}

# Track accounts that have posted Swiss-related content
swiss_accounts = set()
bsky_client = FirehoseSubscribeReposClient()
did_handle_cache = {}

def is_swiss_related(text: str) -> bool:
    """
    Check if a text is related to Switzerland based on keywords and language.
    This heuristic is designed to reduce false positives by requiring language context
    for less specific keywords.
    """
    if not text:
        return False
    text_lower = text.lower()

    # 1. High-confidence check: these words are almost exclusively Swiss-related.
    if any(re.search(r'\b' + re.escape(keyword) + r'\b', text_lower) for keyword in HIGH_CONFIDENCE_SWISS_KEYWORDS):
        return True
    
    # 2. Language detection: count common words to guess the language.
    de_words = {'der', 'die', 'das', 'und', 'ein', 'ist', 'in', 'zu', 'von', 'sich'}
    fr_words = {'le', 'la', 'les', 'et', 'un', 'est', 'de', 'en', 'pour', 'que'}
    it_words = {'il', 'la', 'lo', 'le', 'e', 'un', 'è', 'di', 'in', 'che'}
    
    words = set(re.findall(r'\b\w+\b', text_lower))
    de_score = len(words.intersection(de_words))
    fr_score = len(words.intersection(fr_words))
    it_score = len(words.intersection(it_words))

    # Determine if the text is likely in one of the target languages
    is_de = de_score >= 2 and de_score > fr_score and de_score > it_score
    is_fr = fr_score >= 2 and fr_score > de_score and fr_score > it_score
    is_it = it_score >= 2 and it_score > de_score and de_score > fr_score

    # 3. Contextual check: if the language is likely German, French, or Italian,
    # check for contextual keywords (cities, cantons, political parties).
    if is_de or is_fr or is_it:
        if any(re.search(r'\b' + re.escape(keyword) + r'\b', text_lower) for keyword in CONTEXTUAL_SWISS_KEYWORDS):
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

            record_raw = car.blocks.get(op.cid)
            if not record_raw:
                continue
            
            record = models.get_or_create(record_raw, strict=False)
            if not isinstance(record, models.app.bsky.feed.post.Record) or not getattr(record, 'text', None):
                continue
            
            text = record.text
            author_did = commit.repo

            if author_did in swiss_accounts or is_swiss_related(text):
                if author_did not in swiss_accounts:
                    swiss_accounts.add(author_did)
                    logging.info(f"New Swiss-related account found: {author_did}")
                
                author_handle = did_handle_cache.get(author_did)
                if not author_handle:
                    try:
                        # Use public PLC directory to resolve DID without authentication
                        res = requests.get(f'https://plc.directory/{author_did}', timeout=5)
                        res.raise_for_status()
                        did_doc = res.json()
                        handle = None
                        # e.g., "alsoKnownAs": ["at://bsky.app"]
                        if did_doc.get('alsoKnownAs') and did_doc['alsoKnownAs'][0].startswith('at://'):
                            handle = did_doc['alsoKnownAs'][0][5:]  # Remove 'at://'

                        if handle:
                            author_handle = handle
                            did_handle_cache[author_did] = handle
                        else:
                            author_handle = author_did  # Fallback
                    except Exception as e:
                        logging.warning(f"Could not resolve handle for {author_did}: {e}")
                        author_handle = author_did  # Fallback to DID

                raw_timestamp = record.created_at
                if raw_timestamp:
                    try:
                        # Parse ISO string with 'Z' and convert to local time
                        dt_obj = datetime.fromisoformat(raw_timestamp.replace('Z', '+00:00'))
                        formatted_timestamp = dt_obj.astimezone(None).strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        formatted_timestamp = raw_timestamp # fallback to original string
                else:
                    formatted_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                new_message = {
                    'id': len(message_data) + random.random(), # Use random to avoid key collision
                    'timestamp': formatted_timestamp,
                    'message': text,
                    'platform': 'Bluesky',
                    'account': author_handle,
                    'narrative': 'N/A', # Placeholder narrative
                    'score': 0.0 # Placeholder score
                }

                message_queue.put(new_message)

    except Exception as e:
        logging.error(f"Error processing firehose message: {e}", exc_info=True)


def start_firehose_subscription():
    """Starts the BlueSky firehose subscription. This is a blocking call."""
    try:
        bsky_client.start(on_message_callback)
    except Exception as e:
        logging.error(f"Firehose subscription error: {e}", exc_info=True)


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


firehose_thread = None
firehose_state = 'OFFLINE' # OFFLINE, CONNECTING, CONNECTED, DISCONNECTING

def toggle_firehose():
    """Starts or stops the firehose subscription."""
    global firehose_thread, bsky_client, firehose_state
    if firehose_state == 'CONNECTED':
        firehose_state = 'DISCONNECTING'
        logging.info("Stopping firehose subscription...")
        realtime_button.text = 'Disconnecting...'
        realtime_button.disable()
        status_indicator.props('color=amber')
        status_indicator.text = 'DISCONNECTING'
        bsky_client.stop()
    elif firehose_state == 'OFFLINE':
        firehose_state = 'CONNECTING'
        logging.info("Starting firehose subscription thread...")
        bsky_client = FirehoseSubscribeReposClient() # Create new client for a new run
        firehose_thread = threading.Thread(target=start_firehose_subscription, daemon=True)
        firehose_thread.start()
        realtime_button.text = 'Stop Realtime'
        realtime_button.disable()
        status_indicator.props('color=green')
        status_indicator.text = 'CONNECTED'

def check_firehose_status():
    """Periodically checks the firehose thread and client status to update UI."""
    global firehose_thread, firehose_state
    is_alive = firehose_thread and firehose_thread.is_alive()

    if firehose_state == 'CONNECTING':
        if is_alive:
            firehose_state = 'CONNECTED'
            status_indicator.props('color=green')
            status_indicator.text = 'CONNECTED'
            realtime_button.text = 'Stop Realtime'
            realtime_button.enable()
        elif not is_alive:
            firehose_state = 'OFFLINE'
            status_indicator.props('color=red')
            status_indicator.text = 'OFFLINE'
            realtime_button.text = 'Connect Realtime'
            realtime_button.enable()
            firehose_thread = None

    elif firehose_state == 'CONNECTED':
        if not is_alive:
            firehose_state = 'OFFLINE'
            status_indicator.props('color=red')
            status_indicator.text = 'OFFLINE'
            realtime_button.text = 'Connect Realtime'
            realtime_button.enable()
            firehose_thread = None
            logging.warning("Firehose connection lost unexpectedly.")

    elif firehose_state == 'DISCONNECTING':
        if not is_alive:
            firehose_state = 'OFFLINE'
            status_indicator.props('color=red')
            status_indicator.text = 'OFFLINE'
            realtime_button.text = 'Connect Realtime'
            realtime_button.enable()
            firehose_thread = None

# UI layout
with ui.header(elevated=True).classes('bg-primary text-white row items-center'):
    ui.label('Firewatch | Disinfo Narrative Monitor').classes('text-h5')
    ui.space()
    with ui.row().classes('items-center'):
        status_indicator = ui.badge('OFFLINE', color='red').classes('mr-2')
        realtime_button = ui.button('Connect Realtime', on_click=toggle_firehose)
    ui.button(icon='menu').props('flat color=white').classes('ml-4')

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

def update_table_from_queue():
    """Checks the queue for new messages and updates the table."""
    messages_added = False
    try:
        while True:
            message = message_queue.get_nowait()
            message_data.insert(0, message)
            messages_added = True
    except queue.Empty:
        pass  # The queue is empty

    if messages_added:
        table.update()

ui.timer(1.0, update_table_from_queue)
ui.timer(1.0, check_firehose_status)

# Firehose subscription is now manually started via the UI button

ui.run(
    title='Firewatch',
    favicon='<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="orange" viewBox="0 0 16 16"><path d="M8 16c3.314 0 6-2 6-5.5 0-1.5-.5-4-2.5-6 .25 1.5-1.25 2-1.25 2C11 4 9 .5 6 0c.357 2 .5 4-2 6-1.25 1-2 2.729-2 4.5C2 14 4.686 16 8 16Z"/></svg>'
)
