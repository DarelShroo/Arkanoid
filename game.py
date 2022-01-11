import pygame
from settings import *
from sprites import *
import time

from os import path


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption(GAME_TITLE)
        self.screen = pygame.display.set_mode([WIDTH, HEIGHT])
        self.clock = pygame.time.Clock()
        self.load_data()

        self.playing = False

        #levels
        self.level = 0
        self.power = 0
        self.charger = 0
        
        #countdown
        pygame.time.set_timer(pygame.USEREVENT, 1000)

        self.list_scores = []

        self.large_font = pygame.font.SysFont('arial', 100)
        self.small_font = pygame.font.SysFont('arial', 32)
        self.score_font = pygame.font.SysFont('arial', 26)
        self.twentypx_font = pygame.font.SysFont('arial', 20)
        self.countdown_font = pygame.font.SysFont('arial', 30)

    def load_data(self):
        root_folder = path.dirname(__file__)
        img_folder = path.join(root_folder, "img")
        fx_folder = path.join(root_folder, "sound")

        # Load images
        brick_colors = ['blue', 'green', 'grey', 'purple', 'red', 'yellow']
        self.brick_images = []
        for color in brick_colors:
            img = pygame.image.load(
                path.join(img_folder, f"element_{color}_rectangle.png")).convert_alpha()
            self.brick_images.append(img)
        self.ball_image = pygame.image.load(
            path.join(img_folder, "ballBlue.png")).convert_alpha()
        self.pad_image = pygame.image.load(
            path.join(img_folder, "paddleBlu.png")).convert_alpha()
        self.ini_image = pygame.image.load(
            path.join(img_folder, "title.png")).convert_alpha()

        self.ini_image = pygame.transform.scale(self.ini_image, (640, 480))

        # Load FX and MUSIC
        self.bounce_fx = pygame.mixer.Sound(path.join(fx_folder, 'bounce.wav'))
        self.break_fx = pygame.mixer.Sound(path.join(fx_folder, 'break.wav'))
        pygame.mixer.music.load(path.join(fx_folder, 'Adventure.mp3'))

    def start_game(self):
        self.all_sprites = pygame.sprite.Group()
        self.balls = pygame.sprite.Group()
        self.bricks = pygame.sprite.Group()

        self.player = Pad(self, WIDTH // 2, HEIGHT - 64)
        self.ball = Ball(self, WIDTH // 2, HEIGHT - 128)
        self.build_brick_wall()

        #power
        self.score = 0
        self.charger = 0

        #countdown
        self.counter, self.text = 300, '300'.rjust(3)

        self.run()

    def build_brick_wall(self):
        brick_width = self.brick_images[0].get_rect().width
        brick_height = self.brick_images[0].get_rect().height

        for x in range(8):
            for y in range(7):
                brick_x = 90 + brick_width * x + 2*x
                brick_y = 50 + brick_height * y + 2*y
                Brick(self, brick_x, brick_y)

    def run(self):
        self.playing = True
        pygame.mixer.music.play(-1)
        while self.playing:
            clocksecs = self.clock.tick(FPS)
            self.dt = clocksecs / 1000
            self.events()
            self.update()
            self.draw()
            
    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if self.charger >= 1 :
                    if event.key == pygame.K_SPACE:
                        self.multi_ball_powerup()
                        self.charger -= 1
                        self.power = self.power - 100
                        self.counter -= 10
            if event.type == pygame.USEREVENT:
                self.countdown(event)

    def update(self):
        self.update_collisions()
        self.all_sprites.update()

    def hitbox_collide(self, sprite, other):
        return sprite.hitbox.colliderect(other.hitbox)

    def update_collisions(self):
        hits = pygame.sprite.spritecollide(
            self.player, self.balls, False, self.hitbox_collide)
        for ball in hits:
            self.player.hit_ball(ball)

        brick_hits = pygame.sprite.groupcollide(
            self.balls, self.bricks, False, False, self.hitbox_collide)

        # hits -> [(ball, [brick, brick1, brick2]), (ball2, [brick2])...]
        for ball, bricks in brick_hits.items():
            the_brick = bricks[0]
            ball.bounce(the_brick)
            the_brick.hit()
        self.level_up()
    
    def level_up(self):
        if len(self.bricks.sprites()) == 0:
            self.build_brick_wall()
            self.level += 1 
            self.counter += 60

    def multi_ball_powerup(self):
        if len(self.balls.sprites()) == 0:
            return
            
        reference = self.balls.sprites()[0]
        if reference.asleep:
            return

        for _ in range(MULTIBALL_POWERUP):
            ball = Ball(self, reference.position.x, reference.position.y)
            ball.velocity = Vector2(
                reference.velocity.x *
                random.uniform(-0.5, 0.5),
                reference.velocity.y * random.uniform(0.75, 1.25))
            ball.asleep = False

    def ball_lost(self):
        if len(self.balls.sprites()) == 0:
            self.player.velocity = Vector2(0, 0)
            self.ball = Ball(self, self.player.rect.centerx,
                             self.player.rect.top - 32)
            self.power = 0
            self.charger = 0
            self.level = 0
            self.game_over()
            self.in_game_balls = 1

    def sum_score(self, valor):
        self.score = self.score + valor
        self.power = self.power + valor
        if self.power >= 200:
            self.charger += 1
            self.power = 0 
    
    def countdown(self, event):
        self.counter -= 1
        self.text = str(self.counter).rjust(3) if self.counter > 0 else self.game_over()

#
#
# MENU START AND GAME OVER
#
#

    def main_menu(self):
        self.screen.blit(self.ini_image, (0, 0))
        pygame.display.flip()
        pygame.time.delay(1000)
        in_main_menu = True
        while in_main_menu:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    in_main_menu = False
        self.start_game()

    def game_over(self):
        title_text = self.large_font.render("GAME OVER", True, WHITE)

        score_text = self.small_font.render(
            f"Score: {self.score}  (Press any key to continue)", True, WHITE)

        self.list_scores.append(self.score)
        my_best_score = max(self.list_scores)

        best_score = self.small_font.render(
            f"Your best score: {my_best_score}", True, WHITE)

        self.screen.fill(BLACK)
        self.screen.blit(
            title_text, (WIDTH//2 - title_text.get_rect().centerx, HEIGHT//2 - title_text.get_rect().centery - 150))
        
        self.screen.blit(
            best_score, (10, 240))
        
        self.screen.blit(
            score_text, (WIDTH//2 -
                         score_text.get_rect().centerx, HEIGHT//2 + 200))
        pygame.display.flip()
        pygame.time.delay(1000)
        in_gameover_menu = True
        while in_gameover_menu:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    in_gameover_menu = False

        self.start_game()

    def draw(self):
        self.screen.fill(DARKBLUE)
        self.all_sprites.draw(self.screen)

        score_text = self.score_font.render(
            f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (30, 435))

        level_text = self.twentypx_font.render(
            f"LV: {self.level}", True, WHITE)
        self.screen.blit(level_text, (575, 5))

        charger_text = self.twentypx_font.render(
            f"charger: {self.charger}", True, WHITE)
        self.screen.blit(charger_text, (280, 5))

        power_text = self.twentypx_font.render(
            f"power: {self.power}", True, WHITE)
        self.screen.blit(power_text, (20, 5))

        countdown_text = self.countdown_font.render(
            self.text, True, WHITE)
        self.screen.blit(countdown_text, (500, 435))

        pygame.display.flip()

game = Game()
game.main_menu()