import { tiles } from "@/data/tiles";
import { Tile } from "@/types/aac";

/*
 * Related AAC tile suggestions
 *
 * Rules:
 * 1. Important/common concepts have hand-written contextual suggestions.
 * 2. Every other tile automatically receives sensible category fallbacks.
 * 3. Only IDs that actually exist in tiles.ts are returned.
 * 4. The selected tile itself is never suggested.
 * 5. Maximum 4 suggestions are shown.
 */

const specificRelatedTiles: Record<string, string[]> = {
  // =========================================================
  // FOOD / DRINK
  // =========================================================

  food_water: [
    "action_drink",
    "action_want",
    "feeling_thirsty",
    "feeling_more",
  ],

  food_milk: [
    "action_drink",
    "action_want",
    "feeling_more",
    "action_like",
  ],

  food_juice: [
    "action_drink",
    "action_want",
    "feeling_thirsty",
    "feeling_more",
  ],

  food_bottle: [
    "action_drink",
    "food_water",
    "food_milk",
    "food_juice",
  ],

  food_cup: [
    "action_drink",
    "food_water",
    "food_milk",
    "food_juice",
  ],

  food_rice: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "feeling_more",
  ],

  food_roti: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "feeling_more",
  ],

  food_bread: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "action_like",
  ],

  food_egg: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "action_like",
  ],

  food_chicken: [
    "action_eat",
    "action_want",
    "action_like",
    "action_dislike",
  ],

  food_fish: [
    "action_eat",
    "action_want",
    "action_like",
    "action_dislike",
  ],

  food_fruit: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "action_like",
  ],

  // Fruit

  food_apple: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_banana: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_orange: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_mango: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_strawberry: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_grapes: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_watermelon: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_melon: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_guava: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_pomegranate: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_peach: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_pear: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_cherry: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_pineapple: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_lemon: [
    "action_eat",
    "action_like",
    "action_dislike",
    "feeling_more",
  ],

  // Snacks

  food_biscuit: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_chips: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_donut: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_cake: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_chocolate: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_sweet: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_icecream: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  // Vegetables

  food_vegetables: [
    "action_eat",
    "action_want",
    "action_like",
    "action_dislike",
  ],

  food_potato: [
    "action_eat",
    "action_want",
    "action_like",
    "action_dislike",
  ],

  food_tomato: [
    "action_eat",
    "action_want",
    "action_like",
    "action_dislike",
  ],

  food_onion: [
    "action_eat",
    "action_like",
    "action_dislike",
    "feeling_more",
  ],

  food_carrot: [
    "action_eat",
    "action_want",
    "action_like",
    "action_dislike",
  ],

  food_cucumber: [
    "action_eat",
    "action_want",
    "action_like",
    "action_dislike",
  ],

  food_peas: [
    "action_eat",
    "action_want",
    "action_like",
    "action_dislike",
  ],

  food_spinach: [
    "action_eat",
    "action_like",
    "action_dislike",
    "feeling_more",
  ],

  food_cauliflower: [
    "action_eat",
    "action_like",
    "action_dislike",
    "feeling_more",
  ],

  food_cabbage: [
    "action_eat",
    "action_like",
    "action_dislike",
    "feeling_more",
  ],

  food_corn: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  // Meals / extras

  food_soup: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "action_like",
  ],

  food_tea: [
    "action_drink",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_yogurt: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_sandwich: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "action_like",
  ],

  food_burger: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_fries: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  food_cereal: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "action_like",
  ],

  food_dal: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "feeling_more",
  ],

  food_curry: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "feeling_more",
  ],

  food_paratha: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "feeling_more",
  ],

  food_naan: [
    "action_eat",
    "action_want",
    "feeling_hungry",
    "feeling_more",
  ],

  // =========================================================
  // BODY
  // =========================================================

  body_head: [
    "feeling_pain",
    "feeling_sick",
    "feeling_uncomfortable",
    "feeling_help",
  ],

  body_eye: [
    "feeling_pain",
    "feeling_uncomfortable",
    "feeling_help",
    "person_doctor",
  ],

  body_ear: [
    "feeling_pain",
    "feeling_uncomfortable",
    "feeling_help",
    "person_doctor",
  ],

  body_nose: [
    "feeling_sick",
    "feeling_uncomfortable",
    "feeling_help",
    "person_doctor",
  ],

  body_mouth: [
    "feeling_pain",
    "action_eat",
    "action_drink",
    "action_speak",
  ],

  body_tooth: [
    "feeling_pain",
    "feeling_uncomfortable",
    "feeling_help",
    "person_doctor",
  ],

  body_throat: [
    "feeling_pain",
    "feeling_sick",
    "feeling_help",
    "person_doctor",
  ],

  body_stomach: [
    "feeling_pain",
    "feeling_sick",
    "feeling_nauseous",
    "feeling_help",
  ],

  body_chest: [
    "feeling_pain",
    "feeling_sick",
    "feeling_help",
    "person_doctor",
  ],

  body_back: [
    "feeling_pain",
    "feeling_uncomfortable",
    "feeling_help",
    "action_sit",
  ],

  body_hand: [
    "feeling_pain",
    "feeling_help",
    "action_use",
    "action_wash",
  ],

  body_arm: [
    "feeling_pain",
    "feeling_help",
    "feeling_uncomfortable",
    "person_caregiver",
  ],

  body_leg: [
    "feeling_pain",
    "feeling_help",
    "action_sit",
    "person_caregiver",
  ],

  body_knee: [
    "feeling_pain",
    "feeling_help",
    "action_sit",
    "person_caregiver",
  ],

  body_foot: [
    "feeling_pain",
    "feeling_help",
    "action_sit",
    "person_caregiver",
  ],

  body_finger: [
    "feeling_pain",
    "feeling_help",
    "action_use",
    "person_caregiver",
  ],

  body_hair: [
    "action_wash",
    "person_me",
    "action_help",
    "person_caregiver",
  ],

  body_face: [
    "action_wash",
    "feeling_pain",
    "person_me",
    "feeling_uncomfortable",
  ],

  body_body: [
    "feeling_pain",
    "feeling_sick",
    "feeling_uncomfortable",
    "feeling_help",
  ],

  body_neck: [
    "feeling_pain",
    "feeling_uncomfortable",
    "feeling_help",
    "person_doctor",
  ],

  // =========================================================
  // FEELINGS / NEEDS
  // =========================================================

  feeling_happy: [
    "action_play",
    "action_like",
    "person_friend",
    "social_good",
  ],

  feeling_sad: [
    "feeling_help",
    "person_mom",
    "person_dad",
    "person_friend",
  ],

  feeling_angry: [
    "action_stop",
    "feeling_help",
    "feeling_calm",
    "person_caregiver",
  ],

  feeling_scared: [
    "feeling_help",
    "person_mom",
    "person_dad",
    "person_caregiver",
  ],

  feeling_tired: [
    "action_sleep",
    "action_sit",
    "place_bed",
    "feeling_help",
  ],

  feeling_bored: [
    "action_play",
    "action_read",
    "action_watch",
    "personal_games",
  ],

  feeling_excited: [
    "action_play",
    "person_friend",
    "social_good",
    "feeling_happy",
  ],

  feeling_worried: [
    "feeling_help",
    "person_mom",
    "person_dad",
    "person_caregiver",
  ],

  feeling_confused: [
    "feeling_help",
    "person_teacher",
    "social_dont_know",
    "action_speak",
  ],

  feeling_pain: [
    "body_head",
    "body_stomach",
    "body_back",
    "feeling_help",
  ],

  feeling_hungry: [
    "action_eat",
    "food_rice",
    "food_roti",
    "food_fruit",
  ],

  feeling_thirsty: [
    "action_drink",
    "food_water",
    "food_juice",
    "action_want",
  ],

  feeling_hot: [
    "food_water",
    "action_drink",
    "place_inside",
    "feeling_help",
  ],

  feeling_cold: [
    "place_inside",
    "personal_clothes",
    "feeling_help",
    "person_caregiver",
  ],

  feeling_sick: [
    "person_doctor",
    "place_hospital",
    "feeling_help",
    "feeling_pain",
  ],

  feeling_nauseous: [
    "body_stomach",
    "feeling_sick",
    "feeling_help",
    "person_doctor",
  ],

  feeling_need: [
    "action_want",
    "feeling_help",
    "social_please",
    "person_caregiver",
  ],

  feeling_want: [
    "action_want",
    "social_please",
    "feeling_more",
    "social_yes",
  ],

  feeling_different: [
    "social_different",
    "action_find",
    "social_no",
    "action_want",
  ],

  feeling_more: [
    "social_more",
    "action_want",
    "social_again",
    "social_yes",
  ],

  feeling_less: [
    "social_no",
    "action_stop",
    "social_finished",
    "feeling_okay",
  ],

  feeling_finished: [
    "social_finished",
    "action_finish",
    "social_no",
    "social_good",
  ],

  feeling_help: [
    "action_help",
    "person_mom",
    "person_teacher",
    "person_caregiver",
  ],

  feeling_love: [
    "person_mom",
    "person_dad",
    "person_family",
    "person_friend",
  ],

  feeling_uncomfortable: [
    "feeling_help",
    "action_stop",
    "person_caregiver",
    "social_no",
  ],

  feeling_calm: [
    "feeling_okay",
    "action_sit",
    "person_caregiver",
    "social_good",
  ],

  feeling_sleepy: [
    "action_sleep",
    "place_bed",
    "place_bedroom",
    "feeling_tired",
  ],

  feeling_okay: [
    "social_okay",
    "social_yes",
    "social_good",
    "feeling_calm",
  ],

  // =========================================================
  // ACTIONS
  // =========================================================

  action_eat: [
    "food_rice",
    "food_roti",
    "food_fruit",
    "feeling_hungry",
  ],

  action_drink: [
    "food_water",
    "food_milk",
    "food_juice",
    "feeling_thirsty",
  ],

  action_go: [
    "place_home",
    "place_school",
    "place_bathroom",
    "place_outside",
  ],

  action_come: [
    "person_me",
    "place_home",
    "place_inside",
    "social_please",
  ],

  action_want: [
    "food_water",
    "food_fruit",
    "personal_toy",
    "social_please",
  ],

  action_give: [
    "person_me",
    "person_you",
    "social_please",
    "social_thank_you",
  ],

  action_get: [
    "action_want",
    "social_please",
    "person_caregiver",
    "feeling_need",
  ],

  action_make: [
    "action_help",
    "person_caregiver",
    "place_table",
    "social_please",
  ],

  action_play: [
    "place_playground",
    "person_friend",
    "personal_toy",
    "feeling_happy",
  ],

  action_sleep: [
    "place_bed",
    "place_bedroom",
    "feeling_tired",
    "feeling_sleepy",
  ],

  action_sit: [
    "place_chair",
    "feeling_tired",
    "feeling_pain",
    "person_caregiver",
  ],

  action_stand: [
    "action_go",
    "place_outside",
    "feeling_help",
    "person_caregiver",
  ],

  action_read: [
    "personal_book",
    "person_teacher",
    "place_class",
    "action_help",
  ],

  action_write: [
    "place_class",
    "person_teacher",
    "action_help",
    "personal_school",
  ],

  action_listen: [
    "action_speak",
    "person_teacher",
    "personal_music",
    "social_quiet",
  ],

  action_watch: [
    "personal_tv",
    "personal_favorite_show",
    "action_like",
    "feeling_happy",
  ],

  action_help: [
    "person_mom",
    "person_dad",
    "person_teacher",
    "person_caregiver",
  ],

  action_open: [
    "action_help",
    "social_please",
    "person_caregiver",
    "action_want",
  ],

  action_close: [
    "action_help",
    "social_please",
    "person_caregiver",
    "action_finish",
  ],

  action_turn: [
    "action_help",
    "person_caregiver",
    "social_please",
    "action_stop",
  ],

  action_stop: [
    "social_stop",
    "social_no",
    "feeling_uncomfortable",
    "feeling_help",
  ],

  action_start: [
    "social_yes",
    "action_play",
    "action_go",
    "social_my_turn",
  ],

  action_like: [
    "social_yes",
    "social_good",
    "feeling_happy",
    "feeling_more",
  ],

  action_dislike: [
    "social_no",
    "social_bad",
    "action_stop",
    "feeling_uncomfortable",
  ],

  action_find: [
    "social_where",
    "action_help",
    "person_caregiver",
    "feeling_need",
  ],

  action_bring: [
    "action_give",
    "action_get",
    "social_please",
    "person_caregiver",
  ],

  action_take: [
    "action_get",
    "action_go",
    "social_please",
    "person_caregiver",
  ],

  action_use: [
    "action_help",
    "social_please",
    "person_caregiver",
    "feeling_need",
  ],

  action_wash: [
    "place_bathroom",
    "body_hand",
    "body_face",
    "action_help",
  ],

  action_wait: [
    "social_wait",
    "social_okay",
    "person_caregiver",
    "feeling_calm",
  ],

  action_finish: [
    "social_finished",
    "feeling_finished",
    "social_good",
    "action_stop",
  ],

  action_speak: [
    "person_mom",
    "person_dad",
    "person_teacher",
    "person_friend",
  ],

  // =========================================================
  // PLACES
  // =========================================================

  place_home: [
    "action_go",
    "person_mom",
    "person_dad",
    "person_family",
  ],

  place_school: [
    "action_go",
    "person_teacher",
    "person_friend",
    "place_class",
  ],

  place_bathroom: [
    "action_go",
    "action_help",
    "person_caregiver",
    "action_wash",
  ],

  place_bedroom: [
    "action_sleep",
    "place_bed",
    "feeling_sleepy",
    "feeling_tired",
  ],

  place_room: [
    "action_go",
    "place_inside",
    "person_caregiver",
    "action_play",
  ],

  place_kitchen: [
    "action_eat",
    "action_drink",
    "food_water",
    "person_caregiver",
  ],

  place_park: [
    "action_go",
    "action_play",
    "person_friend",
    "feeling_happy",
  ],

  place_hospital: [
    "person_doctor",
    "feeling_sick",
    "feeling_pain",
    "feeling_help",
  ],

  place_clinic: [
    "person_doctor",
    "feeling_sick",
    "feeling_pain",
    "feeling_help",
  ],

  place_car: [
    "action_go",
    "action_sit",
    "place_outside",
    "person_caregiver",
  ],

  place_bus: [
    "action_go",
    "action_sit",
    "place_school",
    "place_outside",
  ],

  place_market: [
    "action_go",
    "action_want",
    "action_get",
    "person_caregiver",
  ],

  place_mosque: [
    "action_go",
    "person_family",
    "social_quiet",
    "place_outside",
  ],

  place_playground: [
    "action_play",
    "person_friend",
    "feeling_happy",
    "place_outside",
  ],

  place_garden: [
    "action_go",
    "action_play",
    "feeling_happy",
    "place_outside",
  ],

  place_bed: [
    "action_sleep",
    "feeling_sleepy",
    "feeling_tired",
    "place_bedroom",
  ],

  place_table: [
    "action_eat",
    "action_sit",
    "food_water",
    "place_chair",
  ],

  place_chair: [
    "action_sit",
    "feeling_tired",
    "place_table",
    "person_caregiver",
  ],

  place_class: [
    "person_teacher",
    "person_classmate",
    "action_read",
    "action_write",
  ],

  place_outside: [
    "action_go",
    "action_play",
    "place_park",
    "person_friend",
  ],

  place_inside: [
    "action_go",
    "place_room",
    "place_home",
    "action_sit",
  ],

  place_shop: [
    "action_go",
    "action_want",
    "action_get",
    "person_caregiver",
  ],

  place_street: [
    "action_go",
    "place_outside",
    "person_caregiver",
    "action_wait",
  ],

  place_therapy_room: [
    "person_therapist",
    "action_help",
    "person_caregiver",
    "feeling_calm",
  ],

  // =========================================================
  // PEOPLE
  // =========================================================

  person_me: [
    "action_want",
    "feeling_hungry",
    "feeling_thirsty",
    "feeling_pain",
  ],

  person_you: [
    "action_speak",
    "action_help",
    "social_your_turn",
    "social_hello",
  ],

  person_mom: [
    "action_help",
    "action_speak",
    "feeling_love",
    "place_home",
  ],

  person_dad: [
    "action_help",
    "action_speak",
    "feeling_love",
    "place_home",
  ],

  person_brother: [
    "action_play",
    "action_speak",
    "feeling_love",
    "place_home",
  ],

  person_sister: [
    "action_play",
    "action_speak",
    "feeling_love",
    "place_home",
  ],

  person_grandmother: [
    "action_speak",
    "feeling_love",
    "place_home",
    "person_family",
  ],

  person_grandfather: [
    "action_speak",
    "feeling_love",
    "place_home",
    "person_family",
  ],

  person_teacher: [
    "action_help",
    "action_speak",
    "place_school",
    "place_class",
  ],

  person_friend: [
    "action_play",
    "action_speak",
    "feeling_happy",
    "place_playground",
  ],

  person_doctor: [
    "feeling_sick",
    "feeling_pain",
    "feeling_help",
    "place_hospital",
  ],

  person_caregiver: [
    "action_help",
    "action_speak",
    "feeling_help",
    "place_home",
  ],

  person_baby: [
    "person_family",
    "place_home",
    "feeling_love",
    "action_help",
  ],

  person_boy: [
    "action_play",
    "action_speak",
    "person_friend",
    "place_school",
  ],

  person_girl: [
    "action_play",
    "action_speak",
    "person_friend",
    "place_school",
  ],

  person_man: [
    "action_speak",
    "action_help",
    "social_hello",
    "person_people",
  ],

  person_woman: [
    "action_speak",
    "action_help",
    "social_hello",
    "person_people",
  ],

  person_family: [
    "person_mom",
    "person_dad",
    "feeling_love",
    "place_home",
  ],

  person_people: [
    "action_speak",
    "social_hello",
    "place_outside",
    "person_friend",
  ],

  person_child: [
    "action_play",
    "place_school",
    "person_friend",
    "feeling_happy",
  ],

  person_he: [
    "action_speak",
    "action_go",
    "action_want",
    "person_man",
  ],

  person_she: [
    "action_speak",
    "action_go",
    "action_want",
    "person_woman",
  ],

  person_they: [
    "action_speak",
    "action_go",
    "action_play",
    "person_people",
  ],

  person_classmate: [
    "action_play",
    "action_speak",
    "place_class",
    "place_school",
  ],

  person_therapist: [
    "action_help",
    "action_speak",
    "place_therapy_room",
    "person_caregiver",
  ],

  person_visitor: [
    "social_hello",
    "action_speak",
    "place_home",
    "person_people",
  ],

  // =========================================================
  // SOCIAL / CORE
  // =========================================================

  social_yes: [
    "action_want",
    "action_like",
    "social_more",
    "social_good",
  ],

  social_no: [
    "action_dislike",
    "action_stop",
    "social_stop",
    "feeling_uncomfortable",
  ],

  social_please: [
    "action_want",
    "action_help",
    "social_more",
    "social_thank_you",
  ],

  social_thank_you: [
    "social_good",
    "feeling_happy",
    "person_friend",
    "person_caregiver",
  ],

  social_sorry: [
    "social_okay",
    "action_speak",
    "person_friend",
    "feeling_sad",
  ],

  social_hello: [
    "person_friend",
    "person_teacher",
    "action_speak",
    "social_good",
  ],

  social_goodbye: [
    "action_go",
    "place_home",
    "person_friend",
    "social_thank_you",
  ],

  social_okay: [
    "social_yes",
    "feeling_okay",
    "feeling_calm",
    "social_good",
  ],

  social_stop: [
    "action_stop",
    "social_no",
    "feeling_uncomfortable",
    "feeling_help",
  ],

  social_wait: [
    "action_wait",
    "feeling_calm",
    "social_okay",
    "person_caregiver",
  ],

  social_help: [
    "action_help",
    "feeling_help",
    "person_caregiver",
    "person_teacher",
  ],

  social_again: [
    "social_more",
    "action_start",
    "action_play",
    "action_speak",
  ],

  social_more: [
    "feeling_more",
    "action_want",
    "social_again",
    "social_please",
  ],

  social_different: [
    "feeling_different",
    "action_find",
    "action_want",
    "social_no",
  ],

  social_good: [
    "action_like",
    "feeling_happy",
    "social_yes",
    "social_more",
  ],

  social_bad: [
    "action_dislike",
    "feeling_sad",
    "social_no",
    "feeling_help",
  ],

  social_dont_know: [
    "feeling_confused",
    "social_what",
    "social_help",
    "person_teacher",
  ],

  social_what: [
    "social_dont_know",
    "action_speak",
    "person_teacher",
    "social_help",
  ],

  social_where: [
    "action_find",
    "action_go",
    "place_home",
    "place_school",
  ],

  social_who: [
    "person_mom",
    "person_dad",
    "person_teacher",
    "person_friend",
  ],

  social_why: [
    "action_speak",
    "person_teacher",
    "social_dont_know",
    "social_help",
  ],

  social_how: [
    "action_help",
    "person_teacher",
    "social_dont_know",
    "action_speak",
  ],

  social_my_turn: [
    "social_your_turn",
    "action_play",
    "action_start",
    "social_wait",
  ],

  social_your_turn: [
    "social_my_turn",
    "action_play",
    "social_wait",
    "social_yes",
  ],

  social_quiet: [
    "action_listen",
    "action_wait",
    "feeling_calm",
    "social_stop",
  ],

  social_finished: [
    "action_finish",
    "feeling_finished",
    "social_good",
    "action_stop",
  ],

  social_mine: [
    "person_me",
    "action_get",
    "social_my_turn",
    "action_want",
  ],

  social_yours: [
    "person_you",
    "action_give",
    "social_your_turn",
    "social_yes",
  ],

  // =========================================================
  // PERSONALIZATION
  // =========================================================

  personal_name: [
    "person_me",
    "action_speak",
    "social_hello",
    "person_friend",
  ],

  personal_age: [
    "person_me",
    "action_speak",
    "social_what",
    "personal_birthday",
  ],

  personal_birthday: [
    "person_me",
    "person_family",
    "feeling_happy",
    "food_cake",
  ],

  personal_favorite_person: [
    "action_like",
    "feeling_love",
    "person_family",
    "person_friend",
  ],

  personal_sibling_name: [
    "person_brother",
    "person_sister",
    "person_family",
    "action_speak",
  ],

  personal_teacher_name: [
    "person_teacher",
    "place_school",
    "place_class",
    "action_speak",
  ],

  personal_therapist_name: [
    "person_therapist",
    "place_therapy_room",
    "action_help",
    "action_speak",
  ],

  personal_friend_name: [
    "person_friend",
    "action_play",
    "action_speak",
    "feeling_happy",
  ],

  personal_caregiver_name: [
    "person_caregiver",
    "action_help",
    "action_speak",
    "feeling_help",
  ],

  personal_favorite_toy: [
    "personal_toy",
    "action_play",
    "action_like",
    "action_want",
  ],

  personal_favorite_food: [
    "action_eat",
    "action_like",
    "action_want",
    "feeling_hungry",
  ],

  personal_favorite_drink: [
    "action_drink",
    "action_like",
    "action_want",
    "feeling_thirsty",
  ],

  personal_favorite_activity: [
    "action_play",
    "action_like",
    "feeling_happy",
    "action_want",
  ],

  personal_favorite_game: [
    "personal_games",
    "action_play",
    "action_like",
    "person_friend",
  ],

  personal_favorite_show: [
    "personal_tv",
    "action_watch",
    "action_like",
    "feeling_happy",
  ],

  personal_favorite_song: [
    "personal_music",
    "action_listen",
    "action_like",
    "feeling_happy",
  ],

  personal_favorite_book: [
    "personal_book",
    "action_read",
    "action_like",
    "person_teacher",
  ],

  personal_comfort_item: [
    "feeling_calm",
    "action_want",
    "feeling_help",
    "person_caregiver",
  ],

  personal_toy: [
    "action_play",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  personal_book: [
    "action_read",
    "action_want",
    "action_like",
    "person_teacher",
  ],

  personal_bag: [
    "action_get",
    "action_take",
    "action_want",
    "place_school",
  ],

  personal_phone: [
    "action_use",
    "action_speak",
    "person_mom",
    "person_dad",
  ],

  personal_clothes: [
    "action_want",
    "action_get",
    "place_home",
    "person_caregiver",
  ],

  personal_home: [
    "place_home",
    "person_family",
    "person_mom",
    "person_dad",
  ],

  personal_school: [
    "place_school",
    "person_teacher",
    "place_class",
    "person_friend",
  ],

  personal_class: [
    "place_class",
    "person_teacher",
    "person_classmate",
    "action_read",
  ],

  personal_favorite_place: [
    "action_go",
    "action_like",
    "feeling_happy",
    "person_family",
  ],

  personal_specific_place: [
    "action_go",
    "action_want",
    "person_caregiver",
    "social_where",
  ],

  personal_morning_routine: [
    "action_wash",
    "action_eat",
    "action_go",
    "place_school",
  ],

  personal_school_routine: [
    "place_school",
    "person_teacher",
    "action_read",
    "action_write",
  ],

  personal_therapy_routine: [
    "person_therapist",
    "place_therapy_room",
    "action_help",
    "person_caregiver",
  ],

  personal_bedtime_routine: [
    "action_sleep",
    "place_bed",
    "place_bedroom",
    "feeling_sleepy",
  ],

  personal_drawing: [
    "action_make",
    "action_like",
    "feeling_happy",
    "place_table",
  ],

  personal_music: [
    "action_listen",
    "action_like",
    "feeling_happy",
    "feeling_more",
  ],

  personal_tv: [
    "action_watch",
    "action_like",
    "feeling_happy",
    "feeling_more",
  ],

  personal_games: [
    "action_play",
    "action_like",
    "person_friend",
    "feeling_happy",
  ],

  personal_custom_1: [
    "action_want",
    "action_like",
    "action_use",
    "social_more",
  ],

  personal_custom_2: [
    "action_want",
    "action_like",
    "action_use",
    "social_more",
  ],

  personal_custom_3: [
    "action_want",
    "action_like",
    "action_use",
    "social_more",
  ],
};

// =========================================================
// FALLBACKS
// =========================================================
// These guarantee that EVERY tile can produce suggestions,
// even if we later add a new tile to tiles.ts.

const categoryFallbacks: Record<string, string[]> = {
  person: [
    "action_speak",
    "action_help",
    "action_want",
    "social_hello",
  ],

  action: [
    "person_me",
    "social_please",
    "feeling_help",
    "social_more",
  ],

  place: [
    "action_go",
    "person_me",
    "person_caregiver",
    "action_want",
  ],

  feeling: [
    "person_me",
    "action_help",
    "person_caregiver",
    "social_please",
  ],

  body: [
    "feeling_pain",
    "feeling_help",
    "person_caregiver",
    "person_doctor",
  ],

  food: [
    "action_eat",
    "action_want",
    "action_like",
    "feeling_more",
  ],

  social: [
    "person_me",
    "action_speak",
    "person_you",
    "social_please",
  ],

  personal: [
    "person_me",
    "action_want",
    "action_like",
    "action_speak",
  ],
};

// =========================================================
// BUILD SAFE RELATED-TILE MAP
// =========================================================

const validTileIds = new Set(tiles.map((tile) => tile.id));

export const relatedTiles: Record<string, string[]> =
  Object.fromEntries(
    tiles.map((tile) => {
      const specific = specificRelatedTiles[tile.id] ?? [];
      const fallback = categoryFallbacks[tile.category] ?? [];

      const suggestions = [...specific, ...fallback]
        .filter(
          (id, index, array) =>
            validTileIds.has(id) &&
            id !== tile.id &&
            array.indexOf(id) === index
        )
        .slice(0, 4);

      return [tile.id, suggestions];
    })
  );

// =========================================================
// HELPER
// =========================================================

export function getRelatedTiles(tileId: string): Tile[] {
  const ids = relatedTiles[tileId] ?? [];

  return ids
    .map((id) => tiles.find((tile) => tile.id === id))
    .filter((tile): tile is Tile => Boolean(tile));
}