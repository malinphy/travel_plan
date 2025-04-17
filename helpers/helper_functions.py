def assemble_conversation(result, new_input):
    if result !=None:
        new_input = result.to_input_list() + [{'content': new_input,
                                                'role': 'user'}]
    else:
        new_input = new_input
    return new_input