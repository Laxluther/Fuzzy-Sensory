from flask import Flask, render_template, request, redirect, url_for
from fuzzy_calculator import FuzzyCalculator  # Import the class from your module

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        num_samples = int(request.form.get('num_samples'))
        # Collect custom attribute names
        attributes = [request.form.get(f'attribute_{i}') for i in range(1, 5)]
        return redirect(url_for('input_samples', num_samples=num_samples, attributes=','.join(attributes)))
    return render_template('index.html')

@app.route('/input_samples/<int:num_samples>/<attributes>', methods=['GET', 'POST'])
def input_samples(num_samples, attributes):
    attributes = attributes.split(',')
    if request.method == 'POST':
        sample_scores = {}
        quality_scores = {}

        # Retrieve sample scores from the form
        for i in range(1, num_samples+1):
            sample_name = f"Sample {i}"
            sample_scores[sample_name] = {}
            for attribute in attributes:
                form_field_name = f"Sample {i}_{attribute}[]"
                scores = request.form.getlist(form_field_name)
                scores = [int(score) for score in scores]
                sample_scores[sample_name][attribute] = scores

        # Retrieve quality scores from the form
        for attribute in attributes:
            form_field_name = f"Quality_{attribute}[]"
            scores = request.form.getlist(form_field_name)
            scores = [int(score) for score in scores]
            quality_scores[attribute] = scores

        # Perform calculations
        calculator = FuzzyCalculator(sample_scores, quality_scores, attributes)
        calculator.compute()
        results = calculator.get_results()

        # Render results page
        return render_template('results.html', results=results, attributes=attributes)

    return render_template('input_samples.html', num_samples=num_samples, attributes=attributes)

if __name__ == '__main__':
    app.run(debug=True)
