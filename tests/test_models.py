"""Тесты классов частиц и расчётов (модуль particles.models)."""
import math

import pytest

from particles.models import (
    SPEED_OF_LIGHT, CalculationResult, Electron, Hadron, Lepton, Neutron,
    Particle, Proton,
)


# Эталонные значения CODATA 2018
@pytest.mark.parametrize("cls, expected", [
    (Electron, -1.75882001076e11),
    (Proton, 9.5788331560e7),
    (Neutron, 0.0),
])
def test_specific_charge(cls, expected):
    assert cls().specific_charge() == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize("cls, expected", [
    (Electron, 2.42631023867e-12),
    (Proton, 1.32140985539e-15),
    (Neutron, 1.31959090581e-15),
])
def test_compton_wavelength(cls, expected):
    assert cls().compton_wavelength() == pytest.approx(expected, rel=1e-9)


def test_reduced_compton_is_lambda_over_2pi():
    e = Electron()
    assert e.reduced_compton_wavelength() == pytest.approx(e.compton_wavelength() / (2 * math.pi))


def test_relativistic_values():
    e = Electron(0.6 * SPEED_OF_LIGHT)          # γ = 1.25
    assert e.lorentz_factor == pytest.approx(1.25)
    assert e.relativistic_mass == pytest.approx(1.25 * e.rest_mass)
    assert e.specific_charge(relativistic=True) == pytest.approx(e.specific_charge() / 1.25)


def test_abstract_classes_cannot_be_instantiated():
    for cls in (Particle, Lepton, Hadron):
        with pytest.raises(TypeError):
            cls()


def test_inheritance_hierarchy():
    assert issubclass(Electron, Lepton) and issubclass(Lepton, Particle)
    assert issubclass(Proton, Hadron) and issubclass(Neutron, Hadron)
    assert Proton().quark_composition == "uud"
    assert Neutron().quark_composition == "udd"
    assert Electron().lepton_number == 1 and Proton().baryon_number == 1


@pytest.mark.parametrize("bad, error", [
    (-1, ValueError), (SPEED_OF_LIGHT, ValueError), (3e9, ValueError),
    ("fast", TypeError), (True, TypeError), (float("nan"), ValueError),
])
def test_velocity_validation(bad, error):
    with pytest.raises(error):
        Electron(bad)
    p = Proton()
    with pytest.raises(error):
        p.velocity = bad


def test_readonly_properties():
    with pytest.raises(AttributeError):
        Electron().rest_mass = 1.0
    with pytest.raises(AttributeError):
        Proton().charge = 0


def test_factory_and_registry():
    assert set(Particle.registry) == {"electron", "proton", "neutron"}
    p = Particle.create(" Proton ", 1000)
    assert isinstance(p, Proton) and p.velocity == 1000.0
    with pytest.raises(ValueError):
        Particle.create("muon")


def test_dunder_methods():
    assert repr(Electron(5.0)) == "Electron(velocity=5.0)"
    assert "Протон" in str(Proton()) and "uud" in str(Proton())
    assert Electron(1) == Electron(1) and Electron(1) != Electron(2)
    assert Electron() != Proton()
    assert sorted([Neutron(), Electron(), Proton()]) == [Electron(), Proton(), Neutron()]
    assert len({Electron(1), Electron(1)}) == 1


def test_calculate_returns_result():
    r = Proton(0.5 * SPEED_OF_LIGHT).calculate()
    assert isinstance(r, CalculationResult)
    assert r.particle == "Протон" and r.beta == pytest.approx(0.5)
    assert len(list(r)) == len(r.as_dict())
    assert "Комптоновская" in str(r)
