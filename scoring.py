def score_offer(offer):
    final_price = offer["base_price"] + offer["shipping"] + offer["tax"]

    price_score = max(0, 100 - final_price)
    trust_score = offer["rating"] * 20
    age_score = min(offer["store_age"] * 10, 50)

    total_score = (
        price_score * 0.4 +
        trust_score * 0.4 +
        age_score * 0.2
    )

    offer["final_price"] = final_price
    offer["score"] = round(total_score, 2)
    return offer
