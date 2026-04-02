import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['mommys_herbal']
products_collection = db['products']

# Optional: clear existing test items? No, let's just append the new items.
# Or actually, we can drop existing stuff if they were just mocks.
# For now let's just insert.

products = [
    {
        'name': "Paddle Wooden Hair Brush",
        'category': 'Comb',
        'price': 275.0,
        'sizes': [],
        'description': "A premium wooden paddle brush ideal for detangling all hair types safely, reducing static, and massaging the scalp.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Oval Wooden Cushion Brush",
        'category': 'Comb',
        'price': 250.0,
        'sizes': [],
        'description': "Gentle oval cushion brush featuring premium dark bristles designed to glide through hair effortlessly, promoting healthy oils.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Lice Kanghi Neem Comb",
        'category': 'Comb',
        'price': 80.0,
        'sizes': [],
        'description': "Finely crafted, dual-sided Neem wood comb specialized for the meticulous removal of lice, nits, and dandruff.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Pocket Bamboo Comb",
        'category': 'Comb',
        'price': 50.0,
        'sizes': [],
        'description': "Conveniently sized, eco-friendly bamboo pocket comb for quick styling and grooming on the go.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Handle Neem Comb",
        'category': 'Comb',
        'price': 80.0,
        'sizes': [],
        'description': "Ergonomically designed Neem wood comb with a comfortable gripping handle for controlled, deep detangling.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Plain Lilly Neem Comb",
        'category': 'Comb',
        'price': 80.0,
        'sizes': [],
        'description': "Classic straight neem comb crafted for precise styling, managing frizz, and improving scalp blood flow natively.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Mommy's Herbal Face Pack",
        'category': 'Other',
        'price': 150.0,
        'sizes': [{'size': '50 gm', 'price': 150.0}, {'size': '100 gm', 'price': 300.0}, {'size': '200 gm', 'price': 600.0}],
        'description': "Organic, homemade face pack finely formulated to target dark spots, control pigmentation, cure pimples, and naturally brighten the skin.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Wooden Neem Pocket Comb",
        'category': 'Comb',
        'price': 40.0,
        'sizes': [],
        'description': "Miniature neem pocket comb with fine teeth for quick touch-ups and beard grooming.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Wooden Neem Regular Comb",
        'category': 'Comb',
        'price': 80.0,
        'sizes': [],
        'description': "Standard, highly durable neem wood daily-use comb suited for overall scalp health and managing medium to thick hair.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Wooden Neem Shampoo Comb",
        'category': 'Comb',
        'price': 60.0,
        'sizes': [],
        'description': "Ultra wide-tooth neem comb designed specifically for in-shower use to evenly distribute shampoo or conditioner and detangle wet hair smoothly.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Wooden Neem Toothbrush",
        'category': 'Other',
        'price': 30.0,
        'sizes': [],
        'description': "100% eco-friendly neem wood toothbrush featuring soft, charcoal-infused bristles that are gentle on the gums and intense on plaque.",
        'image_url': '',
        'is_out_of_stock': False
    },
    {
        'name': "Bamboo Tongue Cleaner",
        'category': 'Other',
        'price': 30.0,
        'sizes': [],
        'description': "Natural, sustainable bamboo tongue scraper engineered for optimal oral hygiene and keeping breath fresh all day.",
        'image_url': '',
        'is_out_of_stock': False
    }
]

for product in products:
    exists = products_collection.find_one({'name': product['name']})
    if not exists:
        products_collection.insert_one(product)
        print(f"Inserted: {product['name']}")

print("All actual products populated!")
