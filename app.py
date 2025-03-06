from flask import Flask, render_template, request, redirect, url_for
from fuzzy_calculator import FuzzyCalculator
import pandas as pd

app = Flask(__name__)

def colored_conclusion(df):
    """
    For each column (e.g., 'Sample 1') in the DataFrame, find the row with the max value (fuzzy label).
    Sort samples by their max value in descending order, then build an HTML string
    that color-codes each sample from dark to light.
    """
  
    sample_maxes = {}
    for col in df.columns:
        max_row = df[col].idxmax() 
        max_val = df[col].max()    
        sample_maxes[col] = (max_row, max_val)

    sorted_samples = sorted(sample_maxes.items(), key=lambda x: x[1][1], reverse=True)
    

    colors = ["#8B0000", "#B22222", "#CD5C5C", "#F08080", "#FFA07A", "#FFDAB9"]
    
  
    conclusion_parts = []
    for i, (sample_name, (fuzzy_label, _)) in enumerate(sorted_samples):
    
        color = colors[i] if i < len(colors) else colors[-1]
      
        conclusion_parts.append(
            f'<span style="color: {color}; font-weight: bold;">'
            f'{sample_name} ({fuzzy_label})'
            f'</span>'
        )
    
  
    conclusion_html = " > ".join(conclusion_parts)
    return conclusion_html

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        num_samples = int(request.form.get('num_samples'))
       
        attributes = [request.form.get(f'attribute_{i}') for i in range(1, 5)]
        return redirect(url_for('input_samples', num_samples=num_samples, attributes=','.join(attributes)))
    return render_template('index.html')

@app.route('/input_samples/<int:num_samples>/<attributes>', methods=['GET', 'POST'])
def input_samples(num_samples, attributes):
    attributes = attributes.split(',')
    if request.method == 'POST':
        sample_scores = {}
        quality_scores = {}

        for i in range(1, num_samples + 1):
            sample_name = f"Sample {i}"
            sample_scores[sample_name] = {}
            for attribute in attributes:
                form_field_name = f"Sample {i}_{attribute}[]"
                scores = request.form.getlist(form_field_name)
                scores = [int(score) for score in scores]
                sample_scores[sample_name][attribute] = scores

       
        for attribute in attributes:
            form_field_name = f"Quality_{attribute}[]"
            scores = request.form.getlist(form_field_name)
            scores = [int(score) for score in scores]
            quality_scores[attribute] = scores


        calculator = FuzzyCalculator(sample_scores, quality_scores, attributes)
        calculator.compute()
        results = calculator.get_results()

      
        df_samples = results['df_samples']
        df_quality = results['df_quality']

       
        sample_labels = ["Poor (F1)", "Fair (F2)", "Medium (F3)", "Good (F4)", "Very Good (F5)", "Excellent (F6)"]
        df_samples.index = sample_labels
        df_quality.index = sample_labels

       
        results['df_samples'] = df_samples
        results['df_quality'] = df_quality

      
        samples_chart_data = {
            'labels': list(df_samples.columns),
            'datasets': []
        }
        for index in df_samples.index:
            dataset = {
                'label': index,
                'data': list(df_samples.loc[index])
            }
            samples_chart_data['datasets'].append(dataset)

        quality_chart_data = {
            'labels': list(df_quality.columns),
            'datasets': []
        }
        for index in df_quality.index:
            dataset = {
                'label': index,
                'data': list(df_quality.loc[index])
            }
            quality_chart_data['datasets'].append(dataset)

        # Generate colored conclusion lines
        sample_conclusion = colored_conclusion(df_samples)
        quality_conclusion = colored_conclusion(df_quality)

        return render_template(
            'results.html',
            results=results,
            attributes=attributes,
            samples_chart_data=samples_chart_data,
            quality_chart_data=quality_chart_data,
            sample_conclusion=sample_conclusion,
            quality_conclusion=quality_conclusion
        )

    return render_template('input_samples.html', num_samples=num_samples, attributes=attributes)

if __name__ == '__main__':
    app.run(debug=True)
