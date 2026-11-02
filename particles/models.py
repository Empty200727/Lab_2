"""Модуль models — иерархия классов элементарных частиц и физические расчёты.

Что считается (вариант 13):
    * удельный заряд            q / m            [Кл/кг]
    * комптоновская длина волны  λc = h / (m·c)   [м]
    * приведённая комптоновская  ƛc = ħ / (m·c)   [м]
    * при заданной скорости v — лоренц-фактор γ = 1/√(1 − v²/c²),
      релятивистская масса m·γ и релятивистский удельный заряд q / (m·γ).

Иерархия наследования:
    Particle (ABC)
    ├── Lepton (ABC)  → Electron
    └── Hadron (ABC)  → Proton, Neutron
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import total_ordering

# --------------------------------------------------------------------------
# Фундаментальные константы (CODATA 2018, точные значения SI там, где они есть)
# --------------------------------------------------------------------------
SPEED_OF_LIGHT = 299_792_458.0          # c, м/с (точно)
PLANCK_CONSTANT = 6.62607015e-34        # h, Дж·с (точно)
REDUCED_PLANCK = PLANCK_CONSTANT / (2 * math.pi)  # ħ = h / 2π, Дж·с
ELEMENTARY_CHARGE = 1.602176634e-19     # e, Кл (точно)

ELECTRON_MASS = 9.1093837015e-31        # кг
PROTON_MASS = 1.67262192369e-27         # кг
NEUTRON_MASS = 1.67492749804e-27        # кг


# --------------------------------------------------------------------------
# Дескриптор — managed-атрибут скорости
# --------------------------------------------------------------------------
class Velocity:
    """Дескриптор (managed-атрибут) для скорости частицы.

    Проверяет при присваивании, что значение — число и 0 <= v < c.
    Хранит значение в «приватном» атрибуте экземпляра (_velocity).
    """

    def __set_name__(self, owner: type, name: str) -> None:
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, instance, owner=None):
        if instance is None:          # обращение через класс: Particle.velocity
            return self
        return getattr(instance, self.private_name, 0.0)

    def __set__(self, instance, value) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Скорость должна быть числом (м/с)")
        value = float(value)
        if math.isnan(value) or value < 0:
            raise ValueError("Скорость не может быть отрицательной")
        if value >= SPEED_OF_LIGHT:
            raise ValueError("Скорость частицы с массой должна быть меньше скорости света")
        setattr(instance, self.private_name, value)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(0 <= v < {SPEED_OF_LIGHT:.0f} м/с)"


# --------------------------------------------------------------------------
# Результат расчёта
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class CalculationResult:
    """Неизменяемый «снимок» результатов расчёта для одной частицы.

    @dataclass сам генерирует dunder-методы __init__, __repr__, __eq__;
    дополнительно определены __str__ и __iter__.
    """

    particle: str
    symbol: str
    family: str
    velocity: float
    beta: float
    lorentz_factor: float
    rest_mass: float
    relativistic_mass: float
    charge: float
    specific_charge: float
    relativistic_specific_charge: float
    compton_wavelength: float
    reduced_compton_wavelength: float
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(sep=" ", timespec="seconds")
    )

    def as_dict(self) -> dict:
        return asdict(self)

    def __iter__(self):
        """Позволяет распаковывать результат: list(result) / tuple(result)."""
        return iter(self.as_dict().values())

    def __str__(self) -> str:
        return (
            f"Частица: {self.particle} ({self.symbol}), {self.family}\n"
            f"  Скорость v                     = {self.velocity:.6e} м/с (β = {self.beta:.6f})\n"
            f"  Лоренц-фактор γ                = {self.lorentz_factor:.9f}\n"
            f"  Масса покоя m₀                 = {self.rest_mass:.6e} кг\n"
            f"  Релятивистская масса m = γ·m₀  = {self.relativistic_mass:.6e} кг\n"
            f"  Заряд q                        = {self.charge:.6e} Кл\n"
            f"  Удельный заряд q/m₀            = {self.specific_charge:.6e} Кл/кг\n"
            f"  Удельный заряд q/(γ·m₀)        = {self.relativistic_specific_charge:.6e} Кл/кг\n"
            f"  Комптоновская длина λc = h/mc  = {self.compton_wavelength:.6e} м\n"
            f"  Приведённая ƛc = ħ/mc          = {self.reduced_compton_wavelength:.6e} м"
        )


# --------------------------------------------------------------------------
# Абстрактный базовый класс
# --------------------------------------------------------------------------
@total_ordering
class Particle(ABC):
    """Абстрактная элементарная частица.

    Наследники обязаны реализовать абстрактные свойства
    name, symbol, rest_mass, charge, family.
    """

    #: реестр конкретных частиц: ключ -> класс (заполняется в __init_subclass__)
    registry: dict[str, type["Particle"]] = {}

    #: managed-атрибут (дескриптор) — скорость частицы, м/с
    velocity = Velocity()

    def __init__(self, velocity: float = 0.0) -> None:
        self.velocity = velocity          # проверку выполняет дескриптор

    def __init_subclass__(cls, key: str | None = None, **kwargs) -> None:
        """Автоматически регистрирует конкретные классы частиц по ключу."""
        super().__init_subclass__(**kwargs)
        if key is not None:
            cls.key = key
            Particle.registry[key] = cls

    # ---- абстрактные свойства (обязательны для наследников) ----
    @property
    @abstractmethod
    def name(self) -> str:
        """Название частицы по-русски."""

    @property
    @abstractmethod
    def symbol(self) -> str:
        """Обозначение частицы."""

    @property
    @abstractmethod
    def rest_mass(self) -> float:
        """Масса покоя, кг."""

    @property
    @abstractmethod
    def charge(self) -> float:
        """Электрический заряд, Кл."""

    @property
    @abstractmethod
    def family(self) -> str:
        """Семейство частиц (лептон / адрон)."""

    # ---- managed-атрибуты, вычисляемые на лету (только чтение) ----

    @property
    def beta(self) -> float:
        """β = v / c."""
        return self.velocity / SPEED_OF_LIGHT

    @property
    def lorentz_factor(self) -> float:
        """γ = 1 / √(1 − β²)."""
        return 1.0 / math.sqrt(1.0 - self.beta ** 2)

    @property
    def relativistic_mass(self) -> float:
        """m = γ · m₀, кг."""
        return self.lorentz_factor * self.rest_mass

    # ---- расчётные методы ----
    def specific_charge(self, relativistic: bool = False) -> float:
        """Удельный заряд q/m, Кл/кг (при relativistic=True — q/(γ·m₀))."""
        mass = self.relativistic_mass if relativistic else self.rest_mass
        return self.charge / mass

    def compton_wavelength(self) -> float:
        """Комптоновская длина волны λc = h / (m₀·c), м."""
        return self.compton_wavelength_for_mass(self.rest_mass)

    def reduced_compton_wavelength(self) -> float:
        """Приведённая комптоновская длина волны ƛc = ħ / (m₀·c) = λc / 2π, м."""
        return REDUCED_PLANCK / (self.rest_mass * SPEED_OF_LIGHT)

    @staticmethod
    def compton_wavelength_for_mass(mass: float) -> float:
        """λc = h / (m·c) для произвольной массы (кг)."""
        if mass <= 0:
            raise ValueError("Масса должна быть положительной")
        return PLANCK_CONSTANT / (mass * SPEED_OF_LIGHT)

    @classmethod
    def create(cls, key: str, velocity: float = 0.0) -> "Particle":
        """Фабрика: создать частицу по ключу ('electron', 'proton', 'neutron')."""
        try:
            particle_cls = cls.registry[key.strip().lower()]
        except KeyError:
            raise ValueError(
                f"Неизвестная частица '{key}'. Доступны: {', '.join(cls.registry)}"
            ) from None
        return particle_cls(velocity)

    def calculate(self) -> CalculationResult:
        """Выполнить все расчёты и вернуть результат одним объектом."""
        return CalculationResult(
            particle=self.name,
            symbol=self.symbol,
            family=self.family,
            velocity=self.velocity,
            beta=self.beta,
            lorentz_factor=self.lorentz_factor,
            rest_mass=self.rest_mass,
            relativistic_mass=self.relativistic_mass,
            charge=self.charge,
            specific_charge=self.specific_charge(),
            relativistic_specific_charge=self.specific_charge(relativistic=True),
            compton_wavelength=self.compton_wavelength(),
            reduced_compton_wavelength=self.reduced_compton_wavelength(),
        )

    # ---- dunder-методы ----
    def __repr__(self) -> str:
        return f"{type(self).__name__}(velocity={self.velocity!r})"

    def __str__(self) -> str:
        return f"{self.name} ({self.symbol}), v = {self.velocity:.3e} м/с"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Particle):
            return NotImplemented
        return type(self) is type(other) and self.velocity == other.velocity

    def __lt__(self, other: "Particle") -> bool:
        """Сравнение частиц по релятивистской массе (sorted() работает «из коробки»)."""
        if not isinstance(other, Particle):
            return NotImplemented
        return self.relativistic_mass < other.relativistic_mass

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.velocity))


# --------------------------------------------------------------------------
# Промежуточные абстрактные классы
# --------------------------------------------------------------------------
class Lepton(Particle, ABC):
    """Лептон — фундаментальная частица, не участвующая в сильном взаимодействии."""

    def __init__(self, velocity: float = 0.0) -> None:
        super().__init__(velocity)
        self._lepton_number = 1

    @property
    def family(self) -> str:
        return "Лептон"

    @property
    def lepton_number(self) -> int:
        """Лептонное число (только чтение)."""
        return self._lepton_number

    def __str__(self) -> str:
        return f"[Лептон] {super().__str__()}"


class Hadron(Particle, ABC):
    """Адрон (барион) — составная частица из кварков."""

    def __init__(self, velocity: float = 0.0) -> None:
        super().__init__(velocity)
        self._baryon_number = 1

    @property
    def family(self) -> str:
        return "Адрон (барион)"

    @property
    def baryon_number(self) -> int:
        """Барионное число (только чтение)."""
        return self._baryon_number

    @property
    @abstractmethod
    def quark_composition(self) -> str:
        """Кварковый состав, например 'uud'."""

    def __str__(self) -> str:
        return f"[Адрон {self.quark_composition}] {super().__str__()}"


# --------------------------------------------------------------------------
# Конкретные частицы
# --------------------------------------------------------------------------
class Electron(Lepton, key="electron"):
    """Электрон e⁻."""

    def __init__(self, velocity: float = 0.0) -> None:
        super().__init__(velocity)

    @property
    def name(self):
        """Название."""
        return "Электрон"

    @property
    def symbol(self):
        """Обозначение."""
        return "e⁻"

    @property
    def rest_mass(self):
        """Масса покоя, кг."""
        return ELECTRON_MASS

    @property
    def charge(self):
        """Заряд, Кл."""
        return -ELEMENTARY_CHARGE

    def __repr__(self) -> str:
        return f"Electron(velocity={self.velocity!r})"


class Proton(Hadron, key="proton"):
    """Протон p⁺ (кварки uud)."""

    def __init__(self, velocity: float = 0.0) -> None:
        super().__init__(velocity)

    @property
    def name(self):
        """Название."""
        return "Протон"

    @property
    def symbol(self):
        """Обозначение."""
        return "p⁺"

    @property
    def rest_mass(self):
        """Масса покоя, кг."""
        return PROTON_MASS

    @property
    def charge(self):
        """Заряд, Кл."""
        return ELEMENTARY_CHARGE

    @property
    def quark_composition(self):
        """Кварковый состав."""
        return "uud"

    def __repr__(self) -> str:
        return f"Proton(velocity={self.velocity!r})"


class Neutron(Hadron, key="neutron"):
    """Нейтрон n⁰ (кварки udd). Заряд 0 ⇒ удельный заряд 0."""

    def __init__(self, velocity: float = 0.0) -> None:
        super().__init__(velocity)

    @property
    def name(self):
        """Название."""
        return "Нейтрон"

    @property
    def symbol(self):
        """Обозначение."""
        return "n⁰"

    @property
    def rest_mass(self):
        """Масса покоя, кг."""
        return NEUTRON_MASS

    @property
    def charge(self):
        """Заряд, Кл."""
        return 0.0

    @property
    def quark_composition(self):
        """Кварковый состав."""
        return "udd"

    def __repr__(self) -> str:
        return f"Neutron(velocity={self.velocity!r})"
