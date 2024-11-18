import numpy as np
import pandas as pd

# Define constants
MEMBERSHIP_VALUES = [
    (0, 0, 25), (25, 25, 25), (50, 25, 25), (75, 25, 25), (100, 25, 0)
]

FUZZY_SCALE = [
    [1, 0.5, 0, 0, 0, 0, 0, 0, 0, 0],  # F1
    [0.5, 1, 1, 0.5, 0, 0, 0, 0, 0, 0],  # F2
    [0, 0, 0.5, 1, 1, 0.5, 0, 0, 0, 0],  # F3
    [0, 0, 0, 0, 0.5, 1, 1, 0.5, 0, 0],  # F4
    [0, 0, 0, 0, 0, 0, 0.5, 1, 1, 0.5],  # F5
    [0, 0, 0, 0, 0, 0, 0, 0, 0.5, 1]  # F6
]


class FuzzyCalculator:
    def __init__(self, sample_scores, quality_scores, attributes):
        self.sample_scores = sample_scores
        self.quality_scores = quality_scores
        self.attributes = attributes  # Custom attribute names
        self.triplets = {}
        self.quality_triplets = {}
        self.relative_triplets = {}
        self.overall_triplets = {}
        self.bx_values_samples = {}
        self.bx_values_quality = {}
        self.similarity_measures_samples = {}
        self.similarity_measures_quality = {}
        self.df_samples = None
        self.df_quality = None

    def calculate_triplet(self, scores, membership_values):
        total_scores = sum(scores)
        if total_scores == 0:
            return [0, 0, 0]

        triplet = np.array([0.0, 0.0, 0.0])
        for score, membership in zip(scores, membership_values):
            triplet += np.array(membership) * score

        return (triplet / total_scores).tolist()

    def calculate_overall_triplet(self, sample_triplets, rel_triplets):
        overall_triplet = np.array([0.0, 0.0, 0.0])
        for key in sample_triplets:
            S1 = np.array(sample_triplets[key])
            QRel = np.array(rel_triplets[key])
            first_component = S1[0] * QRel[0]
            second_component = (S1[0] * QRel[1]) + (QRel[0] * S1[1])
            third_component = (S1[0] * QRel[2]) + (QRel[0] * S1[2])
            overall_triplet += np.array([first_component, second_component, third_component])
        return [round(value, 3) for value in overall_triplet]

    def calculate_bx_values(self, a, b, c):
        x_values = [0, 20, 30, 40, 50, 60, 70, 80, 90]  # Importance levels
        bx_values = []

        for i, x in enumerate(x_values):
            if (a - b) <= x <= a:
                bx = (x - (a - b)) / b if b != 0 else 0
            elif a < x <= (a + c):
                bx = ((a + c) - x) / c if c != 0 else 0
            else:
                bx = 0

            # Ensure Bx = 1 if a falls between two x values
            if i > 0 and x_values[i - 1] <= a < x:
                bx_values.append(1)  # Insert 1 for the previous x value
            elif x == a:
                bx = 1  # Set the current value to 1 if x equals a

            bx_values.append(round(bx, 3))

        return bx_values

    def calculate_dot_product(self, vec1, vec2):
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        return np.dot(vec1_np, vec2_np.T)

    def calculate_similarity_measures(self, bx_values):
        similarity_measures = {}

        for sample_name, bx in bx_values.items():
            sample_similarity = []
            bx_dot_product = self.calculate_dot_product(bx, bx)

            for f in FUZZY_SCALE:
                f_b_dot_product = self.calculate_dot_product(f, bx)
                f_self_dot_product = self.calculate_dot_product(f, f)
                max_f_b = max(f_self_dot_product, bx_dot_product)
                similarity_measure = f_b_dot_product / max_f_b if max_f_b != 0 else 0
                sample_similarity.append(round(similarity_measure, 4))

            similarity_measures[sample_name] = sample_similarity

        return similarity_measures

    def compute(self):
        # Step 1: Calculate triplets for each sample and attribute
        self.triplets = {
            sample: {attr: self.calculate_triplet(scores, MEMBERSHIP_VALUES) for attr, scores in attributes.items()}
            for sample, attributes in self.sample_scores.items()
        }

        # Step 2: Calculate triplets for quality attributes
        self.quality_triplets = {
            attr: self.calculate_triplet(scores, MEMBERSHIP_VALUES) for attr, scores in self.quality_scores.items()
        }

        # Step 3: Calculate relative triplets for quality attributes
        quality_sum = sum(values[0] for values in self.quality_triplets.values())
        self.relative_triplets = {
            attr: (np.array(values) / quality_sum).tolist() for attr, values in self.quality_triplets.items()
        } if quality_sum != 0 else {attr: [0, 0, 0] for attr in self.quality_triplets}

        # Step 4: Calculate overall triplets for each sample
        self.overall_triplets = {
            sample: self.calculate_overall_triplet(attributes, self.relative_triplets) for sample, attributes in
            self.triplets.items()
        }

        # Step 5: Calculate Bx values for samples and quality attributes
        self.bx_values_samples = {sample: self.calculate_bx_values(*triplet) for sample, triplet in
                                  self.overall_triplets.items()}
        self.bx_values_quality = {attr: self.calculate_bx_values(*triplet) for attr, triplet in
                                  self.quality_triplets.items()}

        # Step 6: Calculate similarity measures
        self.similarity_measures_samples = self.calculate_similarity_measures(self.bx_values_samples)
        self.similarity_measures_quality = self.calculate_similarity_measures(self.bx_values_quality)

        # Step 7: Generate tables
        sample_names = list(self.sample_scores.keys())
        self.df_samples = pd.DataFrame(self.similarity_measures_samples, index=["F1", "F2", "F3", "F4", "F5", "F6"])
        self.df_quality = pd.DataFrame(self.similarity_measures_quality, index=["F1", "F2", "F3", "F4", "F5", "F6"])

    def get_results(self):
        return {
            'triplets': self.triplets,
            'overall_triplets': self.overall_triplets,
            'bx_values_samples': self.bx_values_samples,
            'similarity_measures_samples': self.similarity_measures_samples,
            'similarity_measures_quality': self.similarity_measures_quality,
            'df_samples': self.df_samples,
            'df_quality': self.df_quality
        }
