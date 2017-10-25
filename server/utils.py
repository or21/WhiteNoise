

def handle_user_input(request):
    input_from_user = {}
    for key in request.values.keys():
        input_from_user[key] = request.values[key]
    input_from_user['target_roi'] = float(input_from_user['target_roi'])
    input_from_user['target_position'] = float(input_from_user['target_position'])
    input_from_user['kw_min_spent'] = float(input_from_user['kw_min_spent'])
    input_from_user['avg_cpa'] = float(input_from_user['avg_cpa'])
    input_from_user['delicate_mode_bid_adj'] = (float(input_from_user['delicate_mode_bid_adj'].split(',')[0]),
                                                float(input_from_user['delicate_mode_bid_adj'].split(',')[1]))
    input_from_user['aggressive_mode_caps'] = (float(input_from_user['aggressive_mode_caps'].split(',')[0]),
                                               float(input_from_user['aggressive_mode_caps'].split(',')[1]))
    return input_from_user
