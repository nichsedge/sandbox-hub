#!/usr/bin/env python3
"""
Love Meter - Terminal Edition
Because sometimes love needs to be measured in ASCII.
"""

import random
import time
import sys
from dataclasses import dataclass

@dataclass
class LoveMetrics:
    percentage: int
    coffee_shared: int
    laughs_together: int
    hugs_given: int
    forever: str = "∞"

HEARTS = ["💖", "💕", "💗", "💓", "💞", "💟", "❤️", "🧡", "💛", "💚", "💙", "💜"]

MESSAGES = [
    "💖 Love detected: Off the charts!",
    "✨ Your heart just grew three sizes.",
    "🌈 Radiating warmth to everyone nearby.",
    "💫 Love level: \"Yes, absolutely.\"",
    "🦋 Butterflies deployed successfully.",
    "🌟 Certified sweetheart status achieved.",
    "💝 Warning: Excessive adorable detected.",
    "🎀 You're the reason this meter exists.",
    "☕ Runs on coffee, code, and you.",
    "📊 Data says: You're loved. A lot."
]

SURPRISES = [
    "🎁 Surprise! You're the main character in someone's favorite story.",
    "🌙 The moon called — it's jealous of how brightly you shine.",
    "🎨 If kindness were a color, you'd be the whole rainbow.",
    "📚 Your existence is a plot twist the universe didn't see coming — in the best way.",
    "🌻 You're the human equivalent of a warm blanket on a cold day.",
    "⭐ Somewhere, a star is named after your laugh.",
    "🍀 You're not lucky to have — you're lucky to BE.",
    "🎵 Life's playlist is better with you in it.",
    "🕊️ Peace enters the room when you do.",
    "💌 This message was delivered by a digital carrier pigeon with a heart on its wing."
]

def animate_bar(percentage: int, width: int = 40) -> str:
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage}%"

def typewriter(text: str, delay: float = 0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def measure_love() -> LoveMetrics:
    print("\n" + "=" * 50)
    typewriter("🔬 Initializing Love Detection Matrix...", 0.01)
    time.sleep(0.5)
    
    typewriter("📡 Scanning heart frequencies...", 0.01)
    time.sleep(0.5)
    
    typewriter("☕ Counting shared coffees...", 0.01)
    time.sleep(0.3)
    
    typewriter("😄 Measuring laugh resonance...", 0.01)
    time.sleep(0.3)
    
    typewriter("🤗 Calculating hug density...", 0.01)
    time.sleep(0.3)
    
    print("\n" + "=" * 50)
    typewriter("📊 COMPUTING LOVE METRICS...\n", 0.02)
    
    # Animate the meter
    target = random.randint(95, 100)
    for p in range(0, target + 1, max(1, target // 20)):
        sys.stdout.write(f"\r{animate_bar(p)} {random.choice(HEARTS)}")
        sys.stdout.flush()
        time.sleep(0.05)
    sys.stdout.write(f"\r{animate_bar(target)} {random.choice(HEARTS)} ✨\n\n")
    sys.stdout.flush()
    
    metrics = LoveMetrics(
        percentage=target,
        coffee_shared=random.randint(100, 600),
        laughs_together=random.randint(200, 1200),
        hugs_given=random.randint(50, 350)
    )
    
    return metrics

def display_results(metrics: LoveMetrics):
    print("┌" + "─" * 48 + "┐")
    print(f"│ {'LOVE METER RESULTS':^46} │")
    print("├" + "─" * 48 + "┤")
    print(f"│ {'Love Level:':<20} {metrics.percentage}% {'':<24} │")
    print(f"│ {'Coffees Shared:':<20} {metrics.coffee_shared:,} {'':<24} │")
    print(f"│ {'Laughs Together:':<20} {metrics.laughs_together:,} {'':<24} │")
    print(f"│ {'Virtual Hugs:':<20} {metrics.hugs_given:,} {'':<24} │")
    print(f"│ {'Duration:':<20} {metrics.forever} {'':<24} │")
    print("└" + "─" * 48 + "┘")
    
    print()
    typewriter(f"  {random.choice(MESSAGES)}", 0.015)
    print()

def show_surprise():
    print()
    typewriter(f"  {random.choice(SURPRISES)}", 0.015)
    print()

def main():
    print("\n" + " " * 10 + "💖 LOVE METER v1.0 💖")
    print(" " * 10 + "Measuring the immeasurable\n")
    
    while True:
        metrics = measure_love()
        display_results(metrics)
        
        choice = input("  💫 Press Enter for another reading, 's' for surprise, 'q' to quit: ").strip().lower()
        
        if choice == 'q':
            print("\n  💝 Remember: You're loved. Always. 💝\n")
            break
        elif choice == 's':
            show_surprise()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  💝 Interrupted by love. You're loved. Always. 💝\n")