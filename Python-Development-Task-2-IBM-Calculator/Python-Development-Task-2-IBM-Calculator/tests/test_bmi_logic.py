"""
Unit Tests for BMI Logic and Input Validation
"""

import math
import pytest
from bmi_logic import (
    calculate_bmi,
    classify_bmi,
    validate_inputs,
    get_healthy_weight_range,
    CATEGORY_COLORS,
    CATEGORY_BG_COLORS
)


class TestBMICalculation:
    """Test mathematical accuracy of BMI calculation formula."""

    def test_standard_bmi_calculation(self):
        # 70 kg, 1.75 m -> 70 / (1.75 ** 2) = 22.85714... -> 22.86
        bmi = calculate_bmi(70, 1.75)
        assert bmi == 22.86

    def test_underweight_calculation(self):
        # 50 kg, 1.70 m -> 50 / (1.70 ** 2) = 17.30103... -> 17.30
        bmi = calculate_bmi(50, 1.70)
        assert bmi == 17.30

    def test_overweight_calculation(self):
        # 80 kg, 1.70 m -> 80 / (1.70 ** 2) = 27.68166... -> 27.68
        bmi = calculate_bmi(80, 1.70)
        assert bmi == 27.68

    def test_obese_calculation(self):
        # 95 kg, 1.70 m -> 95 / (1.70 ** 2) = 32.87197... -> 32.87
        bmi = calculate_bmi(95, 1.70)
        assert bmi == 32.87

    def test_zero_weight_raises_error(self):
        with pytest.raises(ValueError, match="Weight must be greater than zero."):
            calculate_bmi(0, 1.75)

    def test_negative_weight_raises_error(self):
        with pytest.raises(ValueError, match="Weight must be greater than zero."):
            calculate_bmi(-70, 1.75)

    def test_zero_height_raises_error(self):
        with pytest.raises(ValueError, match="Height must be greater than zero."):
            calculate_bmi(70, 0)

    def test_negative_height_raises_error(self):
        with pytest.raises(ValueError, match="Height must be greater than zero."):
            calculate_bmi(70, -1.75)

    def test_non_numeric_types_raise_error(self):
        with pytest.raises(TypeError):
            calculate_bmi("70", 1.75)  # type: ignore
        with pytest.raises(TypeError):
            calculate_bmi(70, "1.75")  # type: ignore

    def test_nan_or_inf_raises_error(self):
        with pytest.raises(ValueError):
            calculate_bmi(float("nan"), 1.75)
        with pytest.raises(ValueError):
            calculate_bmi(70, float("inf"))


class TestBMIClassification:
    """Test WHO category classifications and exact boundary thresholds."""

    def test_boundary_underweight(self):
        cat, color = classify_bmi(18.49)
        assert cat == "Underweight"
        assert color == CATEGORY_COLORS["Underweight"]

    def test_boundary_normal_lower(self):
        cat, color = classify_bmi(18.50)
        assert cat == "Normal"
        assert color == CATEGORY_COLORS["Normal"]

    def test_boundary_normal_upper(self):
        cat, color = classify_bmi(24.99)
        assert cat == "Normal"
        assert color == CATEGORY_COLORS["Normal"]

    def test_boundary_overweight_lower(self):
        cat, color = classify_bmi(25.00)
        assert cat == "Overweight"
        assert color == CATEGORY_COLORS["Overweight"]

    def test_boundary_overweight_upper(self):
        cat, color = classify_bmi(29.99)
        assert cat == "Overweight"
        assert color == CATEGORY_COLORS["Overweight"]

    def test_boundary_obese_lower(self):
        cat, color = classify_bmi(30.00)
        assert cat == "Obese"
        assert color == CATEGORY_COLORS["Obese"]

    def test_high_obese_value(self):
        cat, color = classify_bmi(45.50)
        assert cat == "Obese"
        assert color == CATEGORY_COLORS["Obese"]


class TestHealthyWeightRange:
    """Test healthy weight range calculation helper."""

    def test_healthy_range_calculation(self):
        min_w, max_w = get_healthy_weight_range(1.75)
        # 18.5 * (1.75 ** 2) = 56.65625 -> 56.66
        # 24.9 * (1.75 ** 2) = 76.25625 -> 76.26
        assert min_w == 56.66
        assert max_w == 76.26

    def test_invalid_height_for_healthy_range(self):
        with pytest.raises(ValueError):
            get_healthy_weight_range(0)
        with pytest.raises(ValueError):
            get_healthy_weight_range(-1.5)


class TestInputValidation:
    """Test user input validation rules and error messages."""

    def test_valid_inputs(self):
        name, w, h = validate_inputs("  John Doe  ", "72.5", " 1.80 ")
        assert name == "John Doe"
        assert w == 72.5
        assert h == 1.80

    def test_empty_user_name(self):
        with pytest.raises(ValueError, match="Please enter a valid user name."):
            validate_inputs("", "70", "1.75")
        with pytest.raises(ValueError, match="Please enter a valid user name."):
            validate_inputs("    ", "70", "1.75")
        with pytest.raises(ValueError, match="Please enter a valid user name."):
            validate_inputs(None, "70", "1.75")  # type: ignore

    def test_invalid_weight_string(self):
        with pytest.raises(ValueError, match="Please enter a valid weight."):
            validate_inputs("John", "abc", "1.75")
        with pytest.raises(ValueError, match="Please enter a valid weight."):
            validate_inputs("John", "", "1.75")
        with pytest.raises(ValueError, match="Please enter a valid weight."):
            validate_inputs("John", "   ", "1.75")

    def test_negative_or_zero_weight(self):
        with pytest.raises(ValueError, match="Weight must be greater than zero."):
            validate_inputs("John", "0", "1.75")
        with pytest.raises(ValueError, match="Weight must be greater than zero."):
            validate_inputs("John", "-70", "1.75")

    def test_invalid_height_string(self):
        with pytest.raises(ValueError, match="Please enter a valid height."):
            validate_inputs("John", "70", "abc")
        with pytest.raises(ValueError, match="Please enter a valid height."):
            validate_inputs("John", "70", "")
        with pytest.raises(ValueError, match="Please enter a valid height."):
            validate_inputs("John", "70", "   ")

    def test_negative_or_zero_height(self):
        with pytest.raises(ValueError, match="Height must be greater than zero."):
            validate_inputs("John", "70", "0")
        with pytest.raises(ValueError, match="Height must be greater than zero."):
            validate_inputs("John", "70", "-1.75")

    def test_comma_decimal_inputs(self):
        name, w, h = validate_inputs("Sarah", "65,5", "1,68")
        assert name == "Sarah"
        assert w == 65.5
        assert h == 1.68

    def test_out_of_bounds_extremes(self):
        with pytest.raises(ValueError, match="exceeds realistic limits"):
            validate_inputs("John", "9999", "1.75")
        with pytest.raises(ValueError, match="exceeds realistic limits"):
            validate_inputs("John", "70", "5.0")
