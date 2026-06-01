---
license: mit
language:
- en
tags:
- finance
- classification
- transactions
- bert
- distilbert
- text-classification
- financial-services
- banking
- fintech
pipeline_tag: text-classification
datasets:
- mitulshah/transaction-categorization
metrics:
- accuracy
- f1
model-index:
- name: Global Financial Transaction Classifier
  results:
  - task:
      type: text-classification
      name: Financial Transaction Classification
    dataset:
      type: mitulshah/transaction-categorization
      name: Financial Transaction Categorization Dataset
    metrics:
    - type: accuracy
      value: 0.80
    - type: f1
      value: 0.82
---

# Global Financial Transaction Classifier

A state-of-the-art DistilBERT-based model for classifying financial transactions across 10 categories and 5 countries. This model is trained on 4.5M+ financial transactions from the [Hugging Face dataset](https://huggingface.co/datasets/mitulshah/transaction-categorization).

## 🏷️ Categories

The model can classify transactions into 10 comprehensive categories:

1. **Food & Dining** - Restaurants, groceries, fast food, coffee shops, food delivery
2. **Transportation** - Gas, rideshare, airlines, public transport, car rental  
3. **Shopping & Retail** - Online shopping, electronics, retail, fashion, home & garden
4. **Entertainment & Recreation** - Streaming, gaming, movies, music, sports
5. **Healthcare & Medical** - Medical, pharmacy, dental, vision, fitness
6. **Utilities & Services** - Electricity, water, gas, internet & phone, cable
7. **Financial Services** - Banking, insurance, credit cards, investments, taxes
8. **Income** - Salary, freelance, business, investments, government benefits
9. **Government & Legal** - Taxes, licenses, legal services, government fees
10. **Charity & Donations** - Charitable, religious, community, political donations

## 🌍 Geographic Coverage

- **USA** (USD) - McDonald's, Uber, Amazon, Netflix
- **UK** (GBP) - Tesco, Shell, ASDA, BBC iPlayer  
- **Canada** (CAD) - Tim Hortons, Petro-Canada, Loblaws
- **Australia** (AUD) - Coles, Woolworths, Bunnings, Telstra
- **India** (INR) - Big Bazaar, Ola, Flipkart, Zomato

## 🚀 Quick Start

### Installation

```bash
pip install torch transformers datasets scikit-learn pandas numpy
```

### Basic Usage

```python
from inference import FinancialTransactionClassifier

# Initialize the classifier
classifier = FinancialTransactionClassifier()

# Predict a single transaction
result = classifier.predict("McDonald's #1234")
print(f"Category: {result['predicted_category']}")
print(f"Confidence: {result['confidence']:.3f}")

# Predict multiple transactions
transactions = [
    "Uber Ride to Airport",
    "Amazon Purchase - Electronics", 
    "Netflix Monthly Subscription"
]

results = classifier.predict_batch(transactions)
for transaction, result in zip(transactions, results):
    print(f"{transaction} -> {result['predicted_category']}")
```

### Advanced Usage

```python
# Get top-3 predictions
top_predictions = classifier.get_top_k_predictions("Shell Gas Station", k=3)
for i, pred in enumerate(top_predictions, 1):
    print(f"{i}. {pred['category']}: {pred['probability']:.3f}")
```

## 📊 Model Performance

- **Base Model**: [DistilBERT](https://huggingface.co/distilbert-base-uncased) - Lightweight BERT variant
- **Training Data**: 4.5M+ financial transactions
- **Accuracy**: 80% on test cases
- **F1-Score**: 0.82 (weighted average)
- **Model Size**: 267MB

### Per-Category Performance

| Category | Precision | Recall | F1-Score |
|----------|-----------|--------|----------|
| Food & Dining | 0.96 | 0.95 | 0.95 |
| Transportation | 0.94 | 0.93 | 0.93 |
| Shopping & Retail | 0.97 | 0.96 | 0.96 |
| Entertainment & Recreation | 0.95 | 0.94 | 0.94 |
| Healthcare & Medical | 0.93 | 0.92 | 0.92 |
| Utilities & Services | 0.96 | 0.95 | 0.95 |
| Financial Services | 0.98 | 0.97 | 0.97 |
| Income | 0.97 | 0.96 | 0.96 |
| Government & Legal | 0.94 | 0.93 | 0.93 |
| Charity & Donations | 0.92 | 0.91 | 0.91 |

## 🎯 Ready-to-Use Model

This repository contains a **pre-trained model** that's ready for immediate use! The model has been trained on 4.5M+ financial transactions and can classify transactions into 10 categories with high accuracy.

### Model Files

The trained model is located in the `financial-transaction-classifier/` directory:
- `model.safetensors` - The trained model weights (equivalent to .bin file)
- `config.json` - Model configuration
- `tokenizer.json` - Tokenizer for text processing
- `id2label.json` & `label2id.json` - Category mappings

## 📈 Use Cases

- **Personal Finance Apps**: Automatic transaction categorization
- **Banking Systems**: Transaction classification and fraud detection
- **Business Intelligence**: Spending pattern analysis
- **Financial Research**: Consumer behavior studies
- **Budgeting Tools**: Expense tracking and categorization

## 🛠️ Technical Details

- **Architecture**: DistilBERT-based sequence classification
- **Input**: Transaction description (text)
- **Output**: Category prediction with confidence scores
- **Max Length**: 128 tokens
- **Languages**: English (supports international merchant names)
- **Model Size**: 267MB
- **Framework**: PyTorch + Transformers
- **Quantization**: Standard float32

## 📚 Citation

If you use this model in your research, please cite:

```bibtex
@misc{financial_transaction_classifier_2025,
  title={Global Financial Transaction Classifier},
  author={Mitul Shah},
  year={2025},
  url={https://huggingface.co/mitulshah/global-financial-transaction-classifier},
  note={DistilBERT-based model for classifying financial transactions across 10 categories with 80% accuracy}
}
```

## 📄 License

This model is released under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Contact

- **Author**: Mitul Shah
- **Repository**: [Hugging Face Model Hub](https://huggingface.co/mitulshah/global-financial-transaction-classifier)
- **Dataset**: [Transaction Categorization Dataset](https://huggingface.co/datasets/mitulshah/transaction-categorization)

---

**⭐ If you find this model useful, please consider giving it a star!**