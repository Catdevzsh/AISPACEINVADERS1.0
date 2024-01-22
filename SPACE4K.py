import pygame
import random
import numpy as np
import platform

# Initialize Pygame and mixer for sound
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Constants for screen size, player, enemy, and bullet properties
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
PLAYER_SIZE, ENEMY_SIZE, BULLET_SIZE = 50, 35, 5
ENEMY_COUNT, BULLET_SPEED, PLAYER_SPEED, ENEMY_SPEED, FPS = 10, 5, 5, 1, 60

# Colors
WHITE, RED, GREEN = (255, 255, 255), (255, 0, 0), (0, 255, 0)

# Setup screen and font
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")
font = pygame.font.Font(None, 36)

# Function to generate 2D (stereo) sound effects
def generate_stereo_sound(frequency, duration, pan):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave_left = 0.5 * np.sin(2 * np.pi * frequency * t) * (1 - pan)
    wave_right = 0.5 * np.sin(2 * np.pi * frequency * t) * pan
    stereo_wave = np.vstack((wave_left, wave_right)).T
    stereo_wave = np.ascontiguousarray(stereo_wave, dtype=np.int16)
    sound = pygame.sndarray.make_sound((32767 * stereo_wave).astype(np.int16))
    return sound

# Sound effects with stereo panning (0 = left, 1 = right)
laser_sound = generate_stereo_sound(400, 0.2, 0.5)  # Shooting sound
explosion_sound = generate_stereo_sound(150, 0.5, 0.5)  # Enemy hit sound
game_over_sound = generate_stereo_sound(250, 1, 0.5)  # Game over sound

# File select menu
file_slots = ["File 1", "File 2", "File 3"]
selected_file = 0

def file_select_menu():
    global selected_file
    running = True
    while running:
        screen.fill((0, 0, 0))
        title = font.render("Select File", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))

        for i, file in enumerate(file_slots):
            if i == selected_file:
                file_text = font.render(f"> {file}", True, WHITE)
            else:
                file_text = font.render(file, True, WHITE)
            screen.blit(file_text, (SCREEN_WIDTH // 2 - file_text.get_width() // 2, 100 + i * 40))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_file = max(0, selected_file - 1)
                elif event.key == pygame.K_DOWN:
                    selected_file = min(len(file_slots) - 1, selected_file + 1)
                elif event.key == pygame.K_RETURN:
                    running = False

# Player, enemies, bullets, game state, and score
player = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 2 * PLAYER_SIZE, PLAYER_SIZE, PLAYER_SIZE)
enemies = [pygame.Rect(random.randint(0, SCREEN_WIDTH - ENEMY_SIZE), random.randint(0, SCREEN_HEIGHT // 2), ENEMY_SIZE, ENEMY_SIZE) for _ in range(ENEMY_COUNT)]
bullets, game_over = [], False
score = 0  # Initialize score

# Leaderboard data (temporary storage)
leaderboard = []

# Function to display leaderboard
def display_leaderboard():
    screen.fill((0, 0, 0))
    title = font.render("Leaderboard", True, WHITE)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))

    # Display each score
    for i, entry in enumerate(leaderboard):
        entry_text = font.render(f"{i + 1}. {entry['name']}: {entry['score']}", True, WHITE)
        screen.blit(entry_text, (SCREEN_WIDTH // 2 - entry_text.get_width() // 2, 60 + i * 30))

# Reset game function
def reset_game():
    global player, enemies, bullets, game_over, score
    player = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 2 * PLAYER_SIZE, PLAYER_SIZE, PLAYER_SIZE)
    enemies = [pygame.Rect(random.randint(0, SCREEN_WIDTH - ENEMY_SIZE), random.randint(0, SCREEN_HEIGHT // 2), ENEMY_SIZE, ENEMY_SIZE) for _ in range(ENEMY_COUNT)]
    bullets, game_over = [], False
    score = 0  # Reset score

# Game loop
def main_game_loop():
    global player, enemies, bullets, game_over, score
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_SPACE:
                    reset_game()

        if not game_over:
            # Player movement and shooting
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player.left > 0:
                player.move_ip(-PLAYER_SPEED, 0)
            if keys[pygame.K_RIGHT] and player.right < SCREEN_WIDTH:
                player.move_ip(PLAYER_SPEED, 0)
            if keys[pygame.K_SPACE]:
                bullets.append(pygame.Rect(player.centerx, player.top, BULLET_SIZE, BULLET_SIZE))
                laser_sound.play()

            # Update bullets and enemies
            for bullet in bullets[:]:
                bullet.move_ip(0, -BULLET_SPEED)
                if bullet.bottom < 0:
                    bullets.remove(bullet)
            for enemy in enemies:
                enemy.move_ip(0, ENEMY_SPEED)
                if enemy.colliderect(player):
                    game_over = True
                    game_over_sound.play()
                if enemy.top > SCREEN_HEIGHT:
                    enemies.remove(enemy)
                    enemies.append(pygame.Rect(random.randint(0, SCREEN_WIDTH - ENEMY_SIZE), 0, ENEMY_SIZE, ENEMY_SIZE))

            # Check collisions
            for enemy in enemies[:]:
                for bullet in bullets[:]:
                    if enemy.colliderect(bullet):
                        enemies.remove(enemy)
                        bullets.remove(bullet)
                        explosion_sound.play()
                        score += 10  # Increase score
                        enemies.append(pygame.Rect(random.randint(0, SCREEN_WIDTH - ENEMY_SIZE), 0, ENEMY_SIZE, ENEMY_SIZE))
                        break 

        else:
            # Game over logic
            if not leaderboard:  # Add score to leaderboard once
                computer_name = platform.node() or "Player"
                leaderboard.append({'name': computer_name, 'score': score})
            display_leaderboard()

        # Drawing
        screen.fill((0, 0, 0))
        # Draw score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if not game_over:
            pygame.draw.rect(screen, GREEN, player)
            for bullet in bullets:
                pygame.draw.rect(screen, RED, bullet)
            for enemy in enemies:
                pygame.draw.rect(screen, WHITE, enemy)
        else:
            game_over_text = font.render("GAME OVER - PRESS SPACE TO RESTART", True, WHITE)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        clock.tick(FPS)

# Start the game
file_select_menu()  # Show file select menu first
main_game_loop()  # Then start the main game loop

pygame.quit()
