import random
import pygame

import const
import colors
import graphics
import files

DEATH_EFFECTS_PATH = files.json_path("death_effects")
death_effects = files.json_read(DEATH_EFFECTS_PATH)

BENIGN_EFFECTS_PATH = files.json_path("benign_effects")
benign_effects = files.json_read(BENIGN_EFFECTS_PATH)

ALLERGENS_PATH = files.json_path("allergens")
allergens = files.json_read(ALLERGENS_PATH)

BRANDS_PATH = files.json_path("brands")
brands = files.json_read(BRANDS_PATH)

letters = [chr(a) for a in range(ord('a'), ord('z'))]


def generate_verification_code(length):
    code = []
    for _ in range(length):
        code.append(random.choice(letters))
    code.sort()
    return "".join(code)


def generate_fake_verification_code(length):
    string = generate_verification_code(length)
    code = list(string)

    # Check if the code is all the same letter
    for letter in code:
        if letter != code[0]:
            break
    # If it is, the fake algorithm won't work.  Generate a new code
    else:
        return generate_fake_verification_code(length)

    # Randomly finds two adjacent letters that aren't the same
    i = random.randint(0, length - 2)
    while code[i] == code[i + 1]:
        i = random.randint(0, length - 2)

    # Swaps the two letters
    code[i], code[i + 1] = code[i + 1], code[i]

    return "".join(code)


def verification_code_is_valid(code):
    for i in range(1, len(code)):
        if code[i - 1] > code[i]:
            return False

    return True


for index in range(len(death_effects)):
    death_effects[index] = graphics.colorize(death_effects[index], "r")


TOP_TYPES = 5
TOP_ROUND_SMALL = 0
TOP_ROUND_MEDIUM = 1
TOP_ROUND_LARGE = 2
TOP_BEVEL = 3
TOP_INVERTED = 4

EFFECTS = "effects"
BODY_WIDTH = "body_width"
BODY_HEIGHT = "body_height"
LABEL_HEIGHT = "label_height"
LABEL_Y_OFFSET = "label_y_offset"
TOP_NUM = "top_num"
BOTTOM_NUM = "bottom_num"
CAP_X = "cap_x"
CAP_HEIGHT = "cap_height"
TOTAL_WIDTH = "total_width"
TOTAL_HEIGHT = "total_height"
PALETTE_NUM = "palette_num"

NAME = "name"
CAP_COLOR = "cap_color"
BODY_COLOR = "body_color"
LABEL_COLOR = "label_color"


class Palette:
    def __init__(self, cap_color, body_color, label_color, name):
        self.cap_color = cap_color
        self.body_color = body_color
        self.label_color = label_color
        self._name = name

    def to_dict(self):
        d = {
            NAME: self._name,
            CAP_COLOR: self.cap_color,
            BODY_COLOR: self.body_color,
            LABEL_COLOR: self.label_color
        }
        return d


def palette_from_dict(d):
    name = d[NAME]
    cap_color = tuple(d[CAP_COLOR])
    body_color = tuple(d[BODY_COLOR])
    label_color = tuple(d[LABEL_COLOR])
    palette = Palette(cap_color, body_color, label_color, name)
    return palette


def load_palettes(path):
    palette_list = files.json_read(path)
    palettes = []
    for palette in palette_list:
        palette = palette_from_dict(palette)
        palettes.append(palette)

    return palettes


PALETTES_PATH = files.json_path("bottle_palettes")
PALETTES = load_palettes(PALETTES_PATH)
TRANSPARENT_PALETTE = Palette(colors.TRANSPARENT,
                              colors.TRANSPARENT,
                              colors.TRANSPARENT,
                              "Transparent")


def draw_palette_test(surface, position, bottles_per_row):
    start_x = position[0]
    start_y = position[1]
    x = start_x
    y = start_y

    width = 30
    cap_height = 10
    body_height = 30
    body_y = start_y + cap_height
    label_height = 15
    label_y_offset = 5
    label_y = start_y + cap_height + label_y_offset

    for i, palette in enumerate(PALETTES):

        # Cap
        cap_rect = (x, y, width, cap_height)
        pygame.draw.rect(surface, palette.cap_color, cap_rect)

        # Body
        body_rect = (x, body_y, width, body_height)
        pygame.draw.rect(surface, palette.body_color, body_rect)

        # Label
        label_rect = (x, label_y, width, label_height)
        pygame.draw.rect(surface, palette.label_color, label_rect)

        # Text
        text = graphics.tahoma.render("Test", False, colors.BLACK)
        surface.blit(text, (x + 2, label_y))

        # If the row reaches the last bottle, make a new row of bottles
        if i % bottles_per_row == bottles_per_row - 1:
            x = start_x
            y += cap_height + body_height
            body_y = y + cap_height
            label_y = y + cap_height + label_y_offset

        # Otherwise, move to the next bottle
        else:
            x += width


TOP_COUNT = 6
tops = graphics.load_numbered_sprites(files.png_path("bottle_top_%d"), TOP_COUNT)

BOTTOM_COUNT = 2
bottoms = graphics.load_numbered_sprites(files.png_path("bottle_bottom_%d"), BOTTOM_COUNT)


def draw_wedge(surface, position, sprite, width, color):
    """ Draws a sprite on both sides of a rectangle.

    sprite is a pygame surface.  It will be drawn once on the left, then
    flipped to be drawn on the right.
    """

    # Draws left sprite
    surface.blit(sprite, position)

    # Flips left sprite to make right sprite
    flip_sprite = pygame.transform.flip(sprite, True, False)

    # Draws right sprite
    right_x = position[0] + width - sprite.get_width()
    surface.blit(flip_sprite, (right_x, position[1]))

    # Draws middle rect
    middle_x = position[0] + sprite.get_width()
    middle_width = position[0] + width - sprite.get_width() * 2
    top_rect = (middle_x, position[1], middle_width, sprite.get_height())
    pygame.draw.rect(surface, color, top_rect)


class Bottle:
    """ Defaults to not lethal with no effects. """
    def __init__(self):
        self.has_deadly_effect = False
        self.effects = []
        self.allergens = []
        self.allergies = []
        self.brand = ""
        self._bootleg = False
        self.code = ""
        self.judged_lethal = False

        # Main body
        self.body_width = random.randint(100, 230)
        self.body_height = random.randint(150, 200)

        # Label
        self.label_height = random.randint(75, self.body_height - 30)
        upper_bound = self.body_height - self.label_height - 10
        self.label_y_offset = random.randint(10, upper_bound)

        # Top and bottom curve of the bottle's body
        self.top_num = random.randint(0, len(tops) - 1)
        self.bottom_num = random.randint(0, len(bottoms) - 1)

        # Cap
        top_width = self.top.width
        self.cap_x = random.randint(top_width - 15, top_width - 2)
        self.cap_height = random.randint(20, 30)

        self._total_width = self.body_width
        total_height = 0
        total_height += self.cap_height
        total_height += self.body_height
        total_height += self.top.height
        total_height += self.bottom.height
        self._total_height = total_height
        self._total_size = (self._total_width, self._total_height)

        self.palette_num = random.randint(0, len(PALETTES) - 1)

        self.eaten = False
        self.adds_allergies = []

    @property
    def total_height(self):
        return self._total_height

    @total_height.setter
    def total_height(self, value):
        self._total_height = value
        self._total_size = (self._total_width, value)

    @property
    def total_width(self):
        return self._total_width

    @total_width.setter
    def total_width(self, value):
        self._total_width = value
        self._total_size = (value, self._total_height)

    @property
    def total_size(self):
        return self._total_size

    @total_size.setter
    def total_size(self, value):
        self._total_size = value
        self._total_width = value[0]
        self._total_height = value[1]

    @property
    def top_num(self):
        return self._top_num

    @top_num.setter
    def top_num(self, value):
        if value >= len(tops):
            raise IndexError("The requested top number (%d) is greater than"
                             " the maximum top number (%d)!"
                             % (value, len(tops) - 1)
                             )
        self._top_num = value
        self._top = tops[value]

    @property
    def bottom_num(self):
        return self._bottom_num

    @bottom_num.setter
    def bottom_num(self, value):
        if value >= len(bottoms):
            raise IndexError("The requested bottom number (%d) is greater than"
                             " the maximum bottom number (%d)!"
                             % (value, len(bottoms) - 1)
                             )
        self._bottom_num = value
        self._bottom = bottoms[value]

    @property
    def top(self):
        return self._top

    @property
    def bottom(self):
        return self._bottom

    @property
    def palette_num(self):
        return self._palette_num

    @palette_num.setter
    def palette_num(self, value):
        if value >= len(PALETTES):
            raise IndexError("The requested palette number (%d) is greater than"
                             " the maximum palette number (%d)!"
                             % (value, len(PALETTES) - 1)
                             )
        self._palette_num = value
        self._palette = PALETTES[self._palette_num]

    @property
    def palette(self):
        return self._palette

    def render_text(self, colored=False):
        text = ""
        if self.brand:
            text += "Brand: %s <br> " % self.brand

        if self.allergens:
            text += "Contains: "
            text += ", ".join(self.allergens)
            text += " <br> "

        if self.brand or self.allergens or self.code:
            text += "Side Effects: "
        text += ", ".join(self.effects)
        text += " <br> "

        if self.code:
            text += "Code: %s <br> " % self.code

        # Removes the final <br>
        if text.endswith(" <br> "):
            text = text[:-len(" <br> ")]

        font = graphics.tahoma
        max_width = self.body_width

        if colored:
            return graphics.text_block_color_codes(text, font, max_width - 10)

        else:
            return graphics.text_block(text, font, colors.BLACK, max_width - 10)

    def render_body(self):
        surface = graphics.new_surface(self.total_size)

        # Draws the cap of the bottle
        cap_width = self.body_width - self.cap_x * 2
        cap_rect = (self.cap_x, 0, cap_width, self.cap_height)
        pygame.draw.rect(surface, colors.CAP_PLACEHOLDER, cap_rect)

        # Draws the top of the bottle (the part that curves into the cap)
        top_y = self.cap_height
        color = colors.BODY_PLACEHOLDER
        top_sprite = self.top.render()
        draw_wedge(surface, (0, top_y), top_sprite, self.body_width, color)

        # Draws the body of the bottle
        body_y = top_y + self.top.height
        body_rect = (0, body_y, self.body_width, self.body_height)
        pygame.draw.rect(surface, colors.BODY_PLACEHOLDER, body_rect)

        label_y = body_y + self.label_y_offset
        label_rect = (0, label_y, self.body_width, self.label_height)
        pygame.draw.rect(surface, colors.LABEL_PLACEHOLDER, label_rect)

        # Draws the bottom of the bottle
        bottom_y = body_y + self.body_height
        color = colors.BODY_PLACEHOLDER
        bottom_sprite = self.bottom.render()
        draw_wedge(surface, (0, bottom_y), bottom_sprite, self.body_width, color)

        # Colors in the bottle
        pixel_array = pygame.PixelArray(surface)
        pixel_array.replace(colors.CAP_PLACEHOLDER, self.palette.cap_color)
        pixel_array.replace(colors.BODY_PLACEHOLDER, self.palette.body_color)
        pixel_array.replace(colors.LABEL_PLACEHOLDER, self.palette.label_color)
        pixel_array.close()

        return surface

    def render_downscaled_body(self, scale):
        total_width = self.downscaled_total_width(scale)
        total_height = self.downscaled_total_height(scale)
        surface = graphics.new_surface((total_width, total_height))

        # Draws cap
        cap_x = self.cap_x // scale
        cap_width = total_width - (cap_x * 2)
        cap_height = self.cap_height // scale
        cap_rect = (cap_x, 0, cap_width, cap_height)
        pygame.draw.rect(surface, colors.CAP_PLACEHOLDER, cap_rect)

        # Draws the top of the bottle (the part that curves into the cap)
        top_y = cap_height
        top_width = self.top.width // scale
        top_height = self.top.height // scale
        top_sprite = self.top.render()
        top_scaled = pygame.transform.scale(top_sprite, (top_width, top_height))
        color = colors.BODY_PLACEHOLDER
        draw_wedge(surface, (0, top_y), top_scaled, total_width, color)

        # Draws the body of the bottle
        body_y = top_y + top_height
        body_height = (self.body_height + self.bottom.height) // scale
        body_rect = (0, body_y, total_width, body_height)
        pygame.draw.rect(surface, colors.BODY_PLACEHOLDER, body_rect)

        # Draws the label
        label_y = body_y + (self.label_y_offset // scale)
        label_height = self.label_height // scale
        label_rect = (0, label_y, total_width, label_height)
        pygame.draw.rect(surface, colors.LABEL_PLACEHOLDER, label_rect)

        # Note that the bottom of the bottle does not need to be drawn
        # It is too small, so when scaled down, you can't really see it

        # bottom_y = body_y + body_height
        # bottom_width = self.bottom.single_width // scale
        # bottom_height = self.bottom.single_height
        # bottom_sprite = self.bottom.render()
        # bottom_scaled = pygame.transform.scale(bottom_sprite, (bottom_width, bottom_height))
        # color = colors.LABEL_PLACEHOLDER
        # draw_wedge(surface, (0, bottom_y), bottom_scaled, total_width, color)

        # Colors in the bottle
        pixel_array = pygame.PixelArray(surface)
        pixel_array.replace(colors.CAP_PLACEHOLDER, self.palette.cap_color)
        pixel_array.replace(colors.BODY_PLACEHOLDER, self.palette.body_color)
        pixel_array.replace(colors.LABEL_PLACEHOLDER, self.palette.label_color)
        pixel_array.close()

        return surface

    def downscaled_total_width(self, scale):
        return self.total_width // scale

    def downscaled_total_height(self, scale):
        height = self.cap_height // scale
        height += self.top.height // scale
        height += self.body_height // scale
        height += self.bottom.height // scale
        return height

    def render(self, text_color_codes=False):
        surface = self.render_body()

        label_y = self.cap_height + self.top.height + self.label_y_offset

        # Applies text to the bottle
        side_effects = self.render_text(text_color_codes)
        surface.blit(side_effects, (5, label_y + 3))

        return surface

    def add_benign(self, count):
        # Adds a certain amount of benign effects to this bottle
        for _ in range(count):
            effect = random.choice(benign_effects)
            while effect in self.effects:
                effect = random.choice(benign_effects)
            self.effects.append(effect)

    def add_allergens(self, count):
        for _ in range(count):
            allergen = random.choice(allergens)
            while allergen in self.allergens or allergen in self.allergies:
                allergen = random.choice(allergens)
            self.allergens.append(allergen)

    def add_allergy(self, count):
        for _ in range(count):
            allergen = random.choice(allergens)
            while allergen in self.allergens or allergen in self.allergies:
                allergen = random.choice(allergens)
            self.allergies.append(allergen)
            self.effects.append(allergen + " allergy")

    def add_lethal(self, count):
        self.has_deadly_effect = True
        for _ in range(count):
            effect = random.choice(death_effects)
            while effect in self.effects:
                effect = random.choice(death_effects)
            self.effects.append(effect)

    def add_brand(self):
        self.brand = random.choice(brands)

    def become_bootleg(self):
        self._bootleg = True
        for effect in self.effects:
            if effect in benign_effects:
                duplicate = effect
                break
        else:
            raise Exception("Can't make a bottle with no benign effects "
                            "into a bootleg!")

        self.effects.append(duplicate)

    def add_verification(self):
        self.code = generate_verification_code(random.randint(3, 5))

    def add_fake_verification(self):
        self.code = generate_fake_verification_code(random.randint(3, 5))

    @property
    def bootleg(self):
        return self._bootleg

    def shuffle(self):
        random.shuffle(self.effects)

    def to_dict(self):
        d = {
            EFFECTS: self.effects,

            BODY_WIDTH: self.body_width,
            BODY_HEIGHT: self.body_height,

            LABEL_HEIGHT: self.label_height,
            LABEL_Y_OFFSET: self.label_y_offset,

            TOP_NUM: self.top_num,
            BOTTOM_NUM: self.bottom_num,
            PALETTE_NUM: self.palette_num,

            CAP_X: self.cap_x,
            CAP_HEIGHT: self.cap_height,

            TOTAL_WIDTH: self.total_width,
            TOTAL_HEIGHT: self.total_height,
        }
        return d


def bottle_from_dict(d):
    bottle = Bottle()

    bottle.effects = d[EFFECTS]

    bottle.body_width = d[BODY_WIDTH]
    bottle.body_height = d[BODY_HEIGHT]

    # Label
    bottle.label_height = d[LABEL_HEIGHT]
    bottle.label_y_offset = d[LABEL_Y_OFFSET]

    # Top and bottom curve of the bottle's body
    bottle.top_num = d[TOP_NUM]
    bottle.bottom_num = d[BOTTOM_NUM]

    # Cap
    bottle.cap_x = d[CAP_X]
    bottle.cap_height = d[CAP_HEIGHT]

    bottle.total_width = d[TOTAL_WIDTH]
    bottle.total_height = d[TOTAL_HEIGHT]

    bottle.palette_num = d[PALETTE_NUM]

    return bottle


ghost_bottle = Bottle()
ghost_bottle._palette = TRANSPARENT_PALETTE


class BottleGenerator:

    def __init__(self):
        self.level = 0
        self.bottles_until_safe = random.randint(0, 3)
        self.safes_in_a_row = 0
        self.deadlies_in_a_row = 0

    def next_item(self):

        # Fast level generator
        if self.level == const.INCIDENT_FAST:
            bottle = Bottle()
            bottle.add_benign(random.randint(3, 5))

            if self.bottles_until_safe == 0:
                self.bottles_until_safe = random.randint(0, 3)
            else:
                self.bottles_until_safe -= 1
                bottle.effects.pop()
                bottle.add_lethal(1)

        # Faster level generator
        elif self.level == const.INCIDENT_FASTER:
            bottle = Bottle()

            # The more safes you get in a row, the less likely the next
            # bottle is safe.  Likewise for deadlies.
            # It's impossible to get 6 safes/deadlies in a row.
            safe_chance = 0.5
            safe_chance += self.deadlies_in_a_row * 0.09
            safe_chance -= self.safes_in_a_row * 0.09
            if random.random() < safe_chance:
                self.deadlies_in_a_row = 0
                self.safes_in_a_row += 1
                bottle.add_benign(1)
            else:
                self.deadlies_in_a_row += 1
                self.safes_in_a_row = 0
                bottle.add_lethal(1)

        # Allergen level generator
        elif self.level == const.INCIDENT_ALLERGENS:
            bottle = Bottle()
            bottle.add_allergens(random.randint(1, 3))
            bottle.add_allergy(1)

        # Effects and allergens level generator
        elif self.level == const.INCIDENT_EFFECTS_ALLERGENS or self.level == const.INCIDENT_EFFECTS_ALLERGENS_HARD:
            bottle = Bottle()
            bottle.add_benign(random.randint(3, 5))
            bottle.add_allergens(random.randint(1, 4))

            if random.random() < 0.50:
                bottle.effects.pop()
                bottle.add_allergy(1)

            if self.bottles_until_safe == 0:
                self.bottles_until_safe = random.randint(0, 1)
            else:
                self.bottles_until_safe -= 1
                bottle.effects.pop(0)  # Pop at start so that it doesn't pop the allergy
                bottle.add_lethal(1)

        # Effects and brand level generator
        elif self.level == const.INCIDENT_EFFECTS_BRANDS:
            bottle = Bottle()
            bottle.add_benign(random.randint(3, 5))
            bottle.add_brand()

            if self.bottles_until_safe == 0:
                self.bottles_until_safe = random.randint(0, 2)
            else:
                self.bottles_until_safe -= 1
                bottle.effects.pop()
                bottle.add_lethal(1)

        # Effects, allergens, and brands level generator
        elif self.level == const.INCIDENT_EFFECTS_ALLERGENS_BRANDS:
            bottle = Bottle()
            bottle.add_benign(random.randint(3, 5))
            bottle.add_allergens(random.randint(1, 2))
            bottle.add_brand()

            if random.random() < 0.75:
                bottle.effects.pop()
                bottle.add_allergy(1)

            if self.bottles_until_safe == 0:
                self.bottles_until_safe = random.randint(0, 1)
            else:
                self.bottles_until_safe -= 1
                bottle.effects.pop(0)  # Pop at start so that it doesn't pop the allergy
                bottle.add_lethal(1)

        # Effects and bootlegs level generator
        elif self.level == const.INCIDENT_EFFECTS_BOOTLEGS:
            bottle = Bottle()
            bottle.add_benign(random.randint(5, 8))

            if self.bottles_until_safe == 0:
                self.bottles_until_safe = random.randint(0, 3)
            else:
                self.bottles_until_safe -= 1
                bottle.effects.pop()

                # 70% chance of being a bootleg
                if random.random() < 0.7:
                    bottle.become_bootleg()

                # 30% chance of just being normally deadly
                else:
                    bottle.add_lethal(1)

        # Effects and verification level generator
        elif self.level == const.INCIDENT_EFFECTS_VERIFICATION:
            bottle = Bottle()
            bottle.add_benign(random.randint(3, 5))

            if self.bottles_until_safe == 0:
                self.bottles_until_safe = random.randint(0, 2)
            else:
                self.bottles_until_safe -= 1

                # 70% chance of being a fake code
                if random.random() < 0.7:
                    bottle.add_fake_verification()
                else:
                    bottle.effects.pop()
                    bottle.add_lethal(1)

            # Adds verification, if a fake one hasn't already been made
            if not bottle.code:
                bottle.add_verification()

        # Effects and alternation level generator
        elif self.level == const.INCIDENT_EFFECTS_ALTERNATION:
            bottle = Bottle()
            bottle.add_benign(random.randint(5, 8))

            # The more safes you get in a row, the less likely the next
            # bottle is safe.  Likewise for deadlies.
            # It's impossible to get 4 safes/deadlies in a row.
            safe_chance = 0.5
            safe_chance += self.deadlies_in_a_row * 0.13
            safe_chance -= self.safes_in_a_row * 0.13
            if random.random() < safe_chance:
                self.deadlies_in_a_row = 0
                self.safes_in_a_row += 1
            else:
                self.deadlies_in_a_row += 1
                self.safes_in_a_row = 0
                bottle.effects.pop()
                bottle.add_lethal(1)

        # Effects-only level generator (also includes the hard version)
        else:
            bottle = Bottle()
            bottle.add_benign(random.randint(5, 8))

            if self.bottles_until_safe == 0:
                self.bottles_until_safe = random.randint(0, 3)
            else:
                self.bottles_until_safe -= 1
                bottle.effects.pop()
                bottle.add_lethal(1)

        bottle.shuffle()

        # If the text overflows the label, then extend the label
        text_height = bottle.render_text().get_height()
        if bottle.label_height < text_height + 10:
            bottle.label_height = text_height + 10

            if bottle.label_y_offset + bottle.label_height > bottle.body_height:
                previous = bottle.body_height
                bottle.body_height = bottle.label_y_offset + bottle.label_height + 10
                bottle.total_height += bottle.body_height - previous

        return bottle
