def assemble_conversation(result, new_input):
    if result !=None:
        new_input = result.to_input_list() + [{'content': new_input,
                                                'role': 'user'}]
    else:
        new_input = new_input
    return new_input


def text_maker(res):
    step_agents = ""
    for i in (res.final_output.__dict__['sequence']):
        exp = f"Step : {i.step.explanation}"
        step_agents += f"Step : {i.step.explanation}"
        if hasattr(i, 'agents') and i.agents is not None and len(i.agents) > 0:
            agent_text = f"Agent : {i.agents[0].name}"
            step_agents += f" Agent : {i.agents[0].name} \n"
        else:
            agent_text = "Agent : No agents assigned for this step."
            step_agents += " Agent : No agents assigned for this step.\n"
    return step_agents