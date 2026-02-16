from django.core.management.base import BaseCommand

from core.models import Category, Tag


CATEGORIES = [
    "Arts & Crafts", "Music", "Dance", "Photography", "Painting", "Drawing", "Sculpture",
    "Pottery", "Calligraphy", "Digital Art", "Graphic Design", "Animation", "Filmmaking",
    "Writing", "Poetry", "Book Club", "Language Exchange", "Public Speaking", "Theatre",
    "Comedy", "Gaming", "Board Games", "Card Games", "Chess", "Puzzle Solving", "Esports",
    "VR Gaming", "Coding", "Robotics", "Electronics", "3D Printing", "Woodworking",
    "DIY & Maker", "Home Improvement", "Gardening", "Urban Gardening", "Baking", "Cooking",
    "BBQ & Grilling", "Coffee", "Tea Culture", "Wine Tasting", "Craft Beer", "Fitness",
    "Running", "Cycling", "Hiking", "Camping", "Backpacking", "Climbing", "Swimming",
    "Yoga", "Pilates", "Martial Arts", "Boxing", "Dance Fitness", "Team Sports", "Soccer",
    "Basketball", "Volleyball", "Tennis", "Badminton", "Pickleball", "Skating", "Skiing",
    "Snowboarding", "Surfing", "Kayaking", "Fishing", "Birdwatching", "Nature Walks",
    "Travel", "Road Trips", "Motorcycling", "Cars & Auto", "Fashion", "Beauty & Grooming",
    "Personal Finance", "Investing", "Entrepreneurship", "Career Development", "Networking",
    "Mindfulness", "Meditation", "Volunteering", "Community Service", "Pet Lovers",
    "Dog Walking", "Cat Lovers", "Parenting", "Seniors Social", "Student Life",
    "Startup Founders", "Sustainability", "Zero Waste", "Tech Talks", "Science Club",
]


TAGS = [
    "beginner-friendly", "intermediate", "advanced", "all-levels", "drop-in", "weekly",
    "biweekly", "monthly", "weekend", "weekday", "morning", "afternoon", "evening", "night",
    "indoor", "outdoor", "virtual", "hybrid", "social", "competitive", "casual", "family-friendly",
    "kids-friendly", "teen-friendly", "adults-only", "seniors", "women-only", "men-only",
    "lgbtq-friendly", "newcomers", "free", "paid", "equipment-provided", "bring-your-own",
    "pet-friendly", "wheelchair-accessible", "small-group", "large-group", "networking",
    "hands-on", "workshop", "lecture", "practice", "showcase", "performance", "community",
    "creative", "relaxing", "high-energy", "mindfulness", "outreach", "fundraising",
    "acoustic", "guitar", "piano", "drums", "violin", "singing", "choir", "dj", "music-production",
    "hip-hop", "jazz", "rock", "classical", "salsa", "bachata", "k-pop", "ballroom", "latin",
    "portrait", "landscape-photo", "street-photo", "film-photo", "editing", "lightroom",
    "photoshop", "watercolor", "acrylic", "oil-painting", "sketching", "charcoal", "ink",
    "ceramics", "origami", "knitting", "crochet", "sewing", "embroidery", "quilting",
    "jewelry-making", "candle-making", "soap-making", "wood-carving", "laser-cutting",
    "arduino", "raspberry-pi", "python", "javascript", "django", "react", "web-dev",
    "mobile-dev", "ai", "machine-learning", "data-science", "cybersecurity", "cloud",
    "hackathon", "game-dev", "board-games", "tabletop-rpg", "dnd", "magic-the-gathering",
    "pokemon", "chess", "go", "speedcubing", "strategy", "co-op", "fps", "moba", "battle-royale",
    "baking", "sourdough", "pastry", "desserts", "meal-prep", "vegetarian", "vegan", "gluten-free",
    "bbq", "grilling", "coffee-brewing", "espresso", "latte-art", "tea-ceremony", "mixology",
    "wine", "beer", "whisky", "brunch", "street-food", "international-cuisine", "running",
    "5k", "10k", "half-marathon", "cycling-road", "mountain-bike", "spin", "hiking-easy",
    "hiking-moderate", "hiking-hard", "trail-running", "camping", "backpacking", "climbing-gym",
    "bouldering", "top-rope", "swimming-laps", "open-water", "yoga-vinyasa", "yoga-hatha",
    "pilates-mat", "pilates-reformer", "boxing", "kickboxing", "muay-thai", "bjj", "judo",
    "taekwondo", "karate", "calisthenics", "strength-training", "crossfit", "zumba",
    "basketball", "soccer", "volleyball", "tennis", "badminton", "pickleball", "table-tennis",
    "ice-skating", "roller-skating", "skiing", "snowboarding", "surfing", "kayaking",
    "canoeing", "paddleboarding", "fishing", "birdwatching", "nature-photography", "road-trip",
    "travel-hacks", "budget-travel", "luxury-travel", "camp-van", "motorcycle-rides", "cars",
    "detailing", "fashion", "streetwear", "thrifting", "makeup", "skincare", "haircare",
    "personal-finance", "investing", "stocks", "crypto", "real-estate", "entrepreneurship",
    "freelancing", "resume-review", "job-search", "interview-prep", "public-speaking",
    "leadership", "productivity", "book-club", "poetry", "writing-prompts", "journaling",
    "language-english", "language-french", "language-spanish", "language-arabic", "language-mandarin",
    "meditation", "breathwork", "stress-relief", "mental-health", "volunteering", "charity",
    "clean-up", "sustainability", "zero-waste", "recycling", "gardening", "urban-farming",
    "composting", "dog-lovers", "cat-lovers", "pets", "parenting", "students", "startups",
    "science", "astronomy", "history", "culture", "museum", "local-events",
]


def _normalized_unique(values):
    seen = set()
    result = []
    for value in values:
        name = (value or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(name)
    return result


class Command(BaseCommand):
    help = "Seed a large starter set of categories and tags."

    def handle(self, *args, **options):
        categories = _normalized_unique(CATEGORIES)
        tags = _normalized_unique(TAGS)

        existing_categories = set(Category.objects.values_list("name", flat=True))
        existing_categories_lc = {name.lower() for name in existing_categories}
        category_to_create = [Category(name=name) for name in categories if name.lower() not in existing_categories_lc]

        existing_tags = set(Tag.objects.values_list("name", flat=True))
        existing_tags_lc = {name.lower() for name in existing_tags}
        tags_to_create = [Tag(name=name) for name in tags if name.lower() not in existing_tags_lc]

        Category.objects.bulk_create(category_to_create, ignore_conflicts=True)
        Tag.objects.bulk_create(tags_to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: +{len(category_to_create)} categories, +{len(tags_to_create)} tags."
        ))
        self.stdout.write(
            f"Totals: {Category.objects.count()} categories, {Tag.objects.count()} tags."
        )
