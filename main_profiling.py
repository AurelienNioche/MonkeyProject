from analysis.evolution import Analyst, import_data


def main():

    starting_point = "2016-12-01"  # "2017-03-01

    cond = "pool"  # Choice: "day", "beginning_vs_end", "pool"

    monkey = "Havane"
    data = import_data(monkey=monkey, starting_point=starting_point)

    analyst = Analyst(data=data, monkey=monkey)
    analyst.range_parameter_values = {
        "positive_risk_aversion": [-0.8, 0.8],
        "negative_risk_aversion": [-0.8, 0.8],
        "probability_distortion": [0.5, 1.],
        "loss_aversion": [-0.5, 0.5],
        "temp": [0.1, 0.3]
    }

    analyst.n_values_per_parameter = 2

    analyst.sort_data(cond)
    analyst.run(multi=False)

if __name__ == "__main__":
    main()