from nicegui import ui
import random
import string

# Mock data generation
platforms = ['X', 'Telegram', 'Reddit', 'Bluesky']
narratives = ['Naz', 'Bio', 'Con', 'Rcp', 'Ele', 'War', 'Eco', 'Imm', 'Pol', 'Fin']
accounts = [f'user_{"".join(random.choices(string.ascii_lowercase + string.digits, k=6))}' for _ in range(50)]

def generate_message_data(num_messages=50):
    """Generates mock message data."""
    data = []
    for i in range(num_messages):
        narrative = random.choice(narratives)
        account = random.choice(accounts)
        data.append({
            'id': i,
            'message': f'This is a sample message for narrative {narrative}. ' + ''.join(random.choices(string.ascii_letters + ' ', k=80)),
            'platform': random.choice(platforms),
            'account': account,
            'narrative': narrative,
            'score': round(random.uniform(0.5, 1.0), 2)
        })
    return data

message_data = generate_message_data()

# UI layout
ui.dark_mode().enable()

with ui.header(elevated=True).classes('bg-primary text-white'):
    ui.label('Disinformation Narrative Monitor').classes('text-h5')

# Top panels
with ui.row().classes('w-full no-wrap'):
    # Panel 1: Messages Table
    with ui.card().classes('w-1/2'):
        ui.label('Detected Propaganda Activity').classes('text-h6')
        columns = [
            {'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True, 'max-width': '50px'},
            {'name': 'message', 'label': 'Message', 'field': 'message', 'align': 'left'},
            {'name': 'platform', 'label': 'Platform', 'field': 'platform', 'sortable': True},
            {'name': 'account', 'label': 'Account', 'field': 'account', 'sortable': True},
            {'name': 'narrative', 'label': 'Narrative', 'field': 'narrative', 'sortable': True},
            {'name': 'score', 'label': 'Score', 'field': 'score', 'sortable': True},
        ]
        table = ui.table(columns=columns, rows=message_data, row_key='id', selection='single').classes('h-96')

    # Panel 2: Network Graph
    with ui.card().classes('w-1/2'):
        ui.label('Account Network').classes('text-h6')
        network_view = ui.mermaid('graph TD; A[Select a message];')

# Bottom Panel: Narrative Density Heatmap
with ui.card().classes('w-full'):
    ui.label('Narrative Density Heatmap (last hour)').classes('text-h6')
    with ui.column():
        for narrative in narratives:
            with ui.row().classes('items-center w-full'):
                ui.label(narrative).classes('w-12 font-mono')
                with ui.row().classes('no-wrap border rounded-sm p-1 flex-grow'):
                    for i in range(12): # 12 * 5-minute intervals = 1 hour
                        density = random.randint(0, 20)
                        # Heatmap color from blue (low) to red (high)
                        red = int(255 * (density / 20.0))
                        blue = 255 - red
                        color = f'rgb({red}, 0, {blue})'
                        with ui.tooltip(f'{density} messages in interval {i+1}'):
                            ui.label().classes('w-8 h-8 border').style(f'background-color: {color}')

# Interactivity
def update_network_graph(e):
    """Updates the network graph based on table selection."""
    if not e.selection:
        network_view.content = 'graph TD;\n A[Select a message to see the network]'
        return

    selected_row = e.selection[0]
    account = selected_row['account']

    # Generate a mock network for the narrative
    graph = f'graph TD;\n'
    graph += f'    {account}((("{account}")));\n' # Highlight selected account
    
    # Add some other accounts in the same narrative
    other_accounts = random.sample([acc for acc in accounts if acc != account], k=random.randint(2, 5))
    for other_acc in other_accounts:
        graph += f'    {other_acc};\n'
        if random.random() > 0.5:
            graph += f'    {account} --> {other_acc};\n'
        else:
            graph += f'    {other_acc} --> {account};\n'
    
    network_view.content = graph

table.on('selection', update_network_graph)

# Initial state for network view
network_view.content = 'graph TD;\n A[Select a message to see the network]'

ui.run()
