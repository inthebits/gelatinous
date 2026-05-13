# Grammar Engine Specification

## Overview

The Grammar Engine (`world/grammar.py`) is a standalone utility module providing
English grammar processing — verb conjugation, article handling, pronoun
transformation, possessive formation, and capitalization.

It has **no Evennia dependencies in its core functions**. It is imported by
the emote system, the identity system, the clothing system, the combat
system, and any future system that needs English grammar processing.

This spec is the canonical reference for the engine. The Emote/Pose,
Identity/Recognition, and Clothing specs all delegate grammar concerns here.

---

## Verb Conjugation

Converts base-form verbs to third-person singular present tense.

```python
def conjugate_third_person(verb: str) -> str:
    """Convert base-form verb to third-person singular present.

    Args:
        verb: Base form ("lean", "catch", "try").

    Returns:
        Conjugated form ("leans", "catches", "tries").
    """
```

**Irregular table** (checked first):

| Base Form | Third Person |
|---|---|
| be | is |
| have | has |

**Regular rules** (applied in order after irregular table check):

| # | Rule | Pattern | Example |
|---|---|---|---|
| 1 | Sibilant | Ends in -s, -sh, -ch, -x, -z | pass → passes, push → pushes, catch → catches, fix → fixes, buzz → buzzes |
| 2 | -O ending | Ends in -o | go → goes, do → does, echo → echoes |
| 3 | Consonant + Y | Ends in [consonant] + y | try → tries, carry → carries, fly → flies |
| 4 | Default | Everything else | lean → leans, run → runs, play → plays, say → says |

The function checks the irregular table first, then applies regular rules
in order. Unknown words always receive regular treatment — the system never
refuses to conjugate.

The irregular table is intentionally minimal. English third-person singular
present tense is remarkably regular — only `be` and `have` are truly
irregular for this conjugation. The table is easily extensible if edge
cases emerge.

---

## Article Handling

The engine exposes two article-related helpers:

- `get_article(noun_phrase, definite=False)` — returns just the article
  string (`"a"`, `"an"`, or `"the"`).
- `with_article(noun_phrase, definite=False)` — returns the noun phrase
  prefixed with its article, or bare for indefinite pluralia tantum.

`with_article` is the canonical helper for callers that want a complete
noun phrase. `get_article` remains for callers that need just the article
token.

### Phoneme-aware article selection

```python
import inflect

_engine = inflect.engine()

def get_article(noun_phrase: str, definite: bool = False) -> str:
    """Get the appropriate article for a noun phrase.

    Args:
        noun_phrase: The noun phrase ("lanky man", "athletic dame").
        definite: If True, return "the". If False, return "a"/"an".

    Returns:
        Article string: "a", "an", or "the".
    """
    if definite:
        return "the"
    result = _engine.a(noun_phrase)  # "a lanky man" or "an athletic dame"
    return result.split(" ", 1)[0]   # Extract just the article
```

**Context rules** (applied by callers, not the grammar engine):

- **Indefinite** (default for sdescs): `"a lanky man"`, `"an athletic dame"`
- **Definite** (for targeting / repeated reference): `"the lanky man"`
- **None** (for assigned names and "You"): `"Jorge"` — no article

### Pluralia tantum

Some English nouns exist only — or idiomatically, in sdesc context — in
plural form and reject the indefinite article: `"blue jeans"` is
grammatical, `"*a blue jeans"` is not. The engine maintains a curated
frozenset of such nouns and exposes a detector:

```python
def is_pluralia_tantum(noun_phrase: str) -> bool:
    """Return True if the head noun of *noun_phrase* is pluralia tantum."""
```

**Categories covered:**

| Category | Examples |
|---|---|
| True pluralia tantum garments | jeans, pants, trousers, shorts, leggings, overalls |
| Paired-noun garments (idiomatic plural) | boots, shoes, gloves, socks, sneakers |
| Eyewear | glasses, goggles, sunglasses, binoculars |
| Two-bladed/handled tools | scissors, pliers, tweezers, tongs, shears |

**Head-noun rule.** Detection inspects only the *head* of the noun
phrase — the last token before the first prepositional break (`" in "`,
`" with "`, `" wielding "`, `" wearing "`, `" holding "`). This means
sdesc-style phrases such as `"stocky droog in blue jeans"` are judged
on the wearer (`"droog"`), not the garment (`"jeans"`), so the wearer
still correctly receives `"a"`.

**Why not `inflect.singular_noun`?** The `inflect` library's plural
detection is unreliable for pluralia tantum: it returns `"jean"` for
`"jeans"`. An explicit curated set is the only correct approach.

### Article composition

```python
def with_article(noun_phrase: str, definite: bool = False) -> str:
    """Return *noun_phrase* prefixed with the appropriate article.

    Pluralia-tantum nouns receive no indefinite article — "blue jeans"
    is returned bare, never "*a blue jeans". The definite article "the"
    is grammatical with both singular and plural nouns and is applied
    uniformly when *definite* is True.
    """
```

| Input | `definite=False` | `definite=True` |
|---|---|---|
| `"Black Trenchcoat"` | `"a Black Trenchcoat"` | `"the Black Trenchcoat"` |
| `"Orange Jumpsuit"` | `"an Orange Jumpsuit"` | `"the Orange Jumpsuit"` |
| `"blue jeans"` | `"blue jeans"` | `"the blue jeans"` |
| `"black leather combat boots"` | `"black leather combat boots"` | `"the black leather combat boots"` |
| `"stocky droog in blue jeans"` | `"a stocky droog in blue jeans"` | `"the stocky droog in blue jeans"` |

### Per-item override (deferred)

A future enhancement could allow individual prototypes to override
pluralia-tantum classification via an item attribute (e.g. for an
ironic singular `"Pair O' Jeans"` artifact). This is **deferred** until
a real one-off case demands it; the centralized set is sufficient for
all current prototypes.

---

## Pronoun Transformation

```python
def transform_pronoun(
    pronoun: str,
    target_person: str,
    gender: str = "neutral",
) -> str:
    """Transform a first-person pronoun to the target perspective.

    Args:
        pronoun: First-person pronoun ("I", "me", "my", "mine", "myself").
        target_person: "second" (actor self-view) or "third" (observer view).
        gender: "male", "female", or "neutral". Only used for third person.

    Returns:
        Transformed pronoun string.
    """
```

**Gender mapping** from character `sex` attribute:

```python
GENDER_MAP = {
    "male": "male",
    "female": "female",
    "ambiguous": "neutral",
    "neutral": "neutral",
    "nonbinary": "neutral",
    "other": "neutral",
}
```

See `EMOTE_POSE_SPEC.md` Appendix B for the complete transformation tables.

---

## Possessive Forms

For display names used by the identity system and emote rendering:

```python
def possessive(name: str) -> str:
    """Form the possessive of a name or noun phrase.

    Args:
        name: "Jorge", "a lanky man", "you".

    Returns:
        "Jorge's", "a lanky man's", "your".
    """
```

| Input | Output | Notes |
|---|---|---|
| `"Jorge"` | `"Jorge's"` | Standard possessive |
| `"a lanky man"` | `"a lanky man's"` | Sdesc possessive |
| `"you"` | `"your"` | Pronoun — lookup table |
| `"he"` | `"his"` | Pronoun — lookup table |
| `"she"` | `"her"` | Pronoun — lookup table |
| `"they"` | `"their"` | Pronoun — lookup table |

Pronoun possessives are handled by a lookup table. All other inputs
receive `'s` appended.

---

## Subject-Verb Agreement

The conjugation function pairs with the subject reference:

| Subject | Verb Form | Example |
|---|---|---|
| "You" (actor self-view) | Base form | "You lean back." |
| Named character | Third-person singular | "Jorge leans back." |
| Sdesc (singular) | Third-person singular | "A lanky man leans back." |

The rendering pipeline handles this: if the observer is the actor, use
the base form; otherwise, use `conjugate_third_person()`.

---

## Capitalization

```python
def capitalize_first(text: str) -> str:
    """Capitalise the first alphabetic character of a string."""
```

Unlike `str.capitalize()`, this preserves the case of all subsequent
characters and handles leading non-alpha characters (e.g. opening
quotes). Used by the emote pipeline for sentence-initial rendering.

---

## Default Sdesc Keywords

```python
DEFAULT_SDESC_KEYWORDS = {
    "male": "man",
    "female": "woman",
    "neutral": "person",
}
```

Fallback keyword assigned to new characters based on grammar gender,
when no explicit keyword has been chosen via `@shortdesc`. Keyed by the
output of `GENDER_MAP`, not the raw `sex` attribute.

---

## Testing

All grammar functions are unit-tested in `world/tests/test_grammar.py`
with no Evennia dependencies. Run via:

```
evennia test world.tests.test_grammar
```

Test classes: `TestVerbConjugation`, `TestArticles`,
`TestIsPluraliaTantum`, `TestWithArticle`,
`TestPronounTransformation`, `TestPossessive`, `TestCapitalizeFirst`.
