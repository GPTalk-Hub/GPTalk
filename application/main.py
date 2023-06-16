import gradio as gr
import requests

# The sample data


def get_data():
    try:
        floor_data = requests.get(
            'http://3.144.110.171:8000/building/all').json()
    except:
        return {"no data"}

    return floor_data


floor_data = get_data()


def get_all_data():
    return list(floor_data.keys())


def get_floor_data(floor, name):
    global floor_data
    floor_data = get_data()

    if name == None or name == '':
        return list(floor_data.get(floor, ['No Data']))
    else:
        return floor_data[floor].get(name, ['No Data'])


def get_place_data(floor, name):
    return floor_data[floor].get(name, ['No Data'])


def del_data(floor, name):
    try:
        response = requests.delete(
            'http://3.144.110.171:8000/building/delete?floor=' + floor + '&name=' + name)
        if response.status_code == 200:
            return 'Delete Success'
        else:
            return 'Fail: Check the data and try again'
    except:
        return 'Fail: Check the Input data and try again'


def add_data(floor, name, time, type, tel):
    if floor == None or name == None or floor == '' or name == '':
        return 'Floor and Name must be filled'
    if time == None or time == '':
        time = 'Unknown'
    if type == None or type == '':
        type = 'Unknown'
    if tel == None or tel == '':
        tel = 'Unknown'

    try:
        if floor_data[floor][name]:
            floor_data[floor][name] = {
                'name': name,
                'floor': floor,
                'type': type,
                'operating_time': time,
                'phone_num': tel
            }
            response = requests.put(
                'http://3.144.110.171:8000/building/update?floor=' + floor + '&name=' + name, json=floor_data[floor][name])
            if response.status_code == 200:
                return response.json()
            else:
                return 'Fail: Check the Input data and try again'
    except KeyError:
        new_data = {
            'name': name,
            'floor': floor,
            'type': type,
            'operating_time': time,
            'phone_num': tel
        }
        response = requests.post(
            'http://3.144.110.171:8000/building/add', json=new_data)
        if response.status_code == 200:
            return response.json()
        else:
            return 'Fail: Check the Input data and try again'

    return 'Fail: Check the Input data and try again'


places = []

with gr.Blocks() as main:

    gr.Markdown("Daeyang AI Hall admin page")
    with gr.Tab("Get Floor Info"):
        floor_input = gr.Dropdown(
            choices=get_all_data(), label='Select the Floor')
        name_input = gr.inputs.Textbox(label='Input the name')
        floor_output = gr.Textbox(label='Get Info Result')
        floor_button = gr.Button("Get Info")
    floor_button.click(get_floor_data, inputs=[floor_input, name_input],
                       outputs=floor_output)

    gr.Markdown("Modify the data")
    with gr.Tab("Delete Data"):
        floor_input = gr.inputs.Dropdown(
            choices=get_all_data(), label='Select the floor')
        name_input = gr.inputs.Textbox(
            label='Input the name: If you want to delete the whole floor, leave it blank')
        del_output = gr.outputs.Textbox(label='Delete Result')
        del_button = gr.Button("Delete")
    del_button.click(del_data, inputs=[
                     floor_input, name_input], outputs=del_output)

    with gr.Tab("Modify Data or Add Data"):
        floor_input = gr.inputs.Dropdown(
            choices=get_all_data(), label='Select the floor')
        name_input = gr.inputs.Textbox(
            label='Input the name')
        time_input = gr.inputs.Textbox(
            label='Input the operating time: Unknown for blank')
        type_input = gr.inputs.Textbox(
            label='Input the type: Unknown for blank')
        tel_input = gr.inputs.Textbox(
            label='Input the tel: Unknown for blank')

        add_output = gr.outputs.Textbox(label='Add Result')
        add_button = gr.Button("Add")
    add_button.click(add_data, inputs=[
        floor_input, name_input, time_input, type_input, tel_input], outputs=add_output)


if __name__ == "__main__":
    main.launch(share=True)
