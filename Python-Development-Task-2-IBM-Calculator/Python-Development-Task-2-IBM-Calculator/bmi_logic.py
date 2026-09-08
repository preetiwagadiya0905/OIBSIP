"""
BMI Calculation & Business Logic Module

Handles mathematical calculations, standard WHO categorization,
color-code mappings, and robust input validation.
"""

import math
from typing import Tuple, Dict, Any


# Standard category color palette (accessible, high-contrast hex codes)
CATEGORY_COLORS: Dict[str, str] = {
    "Underweight": "#1976D2",  # Accessible Blue
    "Normal": "#2E7D32",       # Accessible Green
    "Overweight": "#E65100",   # Accessible Orange
    "Obese": "#C62828"         # Accessible Red
}

# Category light background colors for UI cards/badges
CATEGORY_BG_COLORS: Dict[str, str] = {
    "Underweight": "#E3F2FD",  # Light Blue
    "Normal": "#E8F5E9",       # Light Green
    "Overweight": "#FFF3E0",   # Light Orange
    "Obese": "#FFEBEE"         # Light Red
}


def calculate_bmi(weight: float, height: float) -> float:
    """
    Calculate Body Mass Index (BMI).
    
    Formula: BMI = weight / (height ** 2)
    
    Args:
        weight: Body weight in kilograms (kg)
        height: Body height in meters (m)
        
    Returns:
        float: Calculated BMI value rounded to 2 decimal places.
        
    Raises:
        ValueError: If weight <= 0 or height <= 0 or non-finite values.
    """
    if not isinstance(weight, (int, float)) or not isinstance(height, (int, float)):
        raise TypeError("Weight and height must be numeric values.")
    
    if math.isnan(weight) or math.isinf(weight):
        raise ValueError("Weight must be a valid finite number.")
    if math.isnan(height) or math.isinf(height):
        raise ValueError("Height must be a valid finite number.")
        
    if weight <= 0:
        raise ValueError("Weight must be greater than zero.")
    if height <= 0:
        raise ValueError("Height must be greater than zero.")
        
    bmi = weight / (height ** 2)
    return round(bmi, 2)


def classify_bmi(bmi: float) -> Tuple[str, str]:
    """
    Classify BMI into standard categories according to WHO guidelines:
    - Underweight: BMI < 18.5
    - Normal:      18.5 <= BMI < 25.0 (18.5 - 24.9)
    - Overweight:  25.0 <= BMI < 30.0 (25.0 - 29.9)
    - Obese:       BMI >= 30.0
    
    Boundary handling:
    - 18.49 -> Underweight
    - 18.50 -> Normal
    - 24.99 -> Normal
    - 25.00 -> Overweight
    - 29.99 -> Overweight
    - 30.00 -> Obese

    Args:
        bmi: Calculated BMI value
        
    Returns:
        Tuple[str, str]: (Category Name, Hex Color Code)
    """
    if not isinstance(bmi, (int, float)) or math.isnan(bmi) or math.isinf(bmi):
        raise ValueError("BMI must be a valid finite number.")
        
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obese"
        
    color = CATEGORY_COLORS[category]
    return category, color


def get_healthy_weight_range(height: float) -> Tuple[float, float]:
    """
    Calculate the healthy weight range (BMI 18.5 - 24.9) in kg for a given height.
    
    Args:
        height: Height in meters
        
    Returns:
        Tuple[float, float]: (min_healthy_weight_kg, max_healthy_weight_kg)
    """
    if height <= 0:
        raise ValueError("Height must be greater than zero.")
    min_weight = round(18.5 * (height ** 2), 2)
    max_weight = round(24.9 * (height ** 2), 2)
    return min_weight, max_weight


def validate_inputs(user_name: str, weight_str: str, height_str: str) -> Tuple[str, float, float]:
    """
    Validate user inputs from GUI form fields.
    
    Checks for:
    - Non-empty, trimmed user name.
    - Valid numeric positive weight.
    - Valid numeric positive height.
    
    Args:
        user_name: Raw string from user name entry
        weight_str: Raw string from weight entry
        height_str: Raw string from height entry
        
    Returns:
        Tuple[str, float, float]: (cleaned_user_name, valid_weight, valid_height)
        
    Raises:
        ValueError: With specific, friendly error messages on invalid input.
    """
    # 1. Validate User Name
    if user_name is None:
        raise ValueError("Please enter a valid user name.")
    
    cleaned_name = user_name.strip()
    if not cleaned_name:
        raise ValueError("Please enter a valid user name.")

    # 2. Validate Weight
    if weight_str is None or not str(weight_str).strip():
        raise ValueError("Please enter a valid weight.")
    
    clean_w_str = str(weight_str).strip().replace(",", ".")
    try:
        weight = float(clean_w_str)
    except (ValueError, TypeError):
        raise ValueError("Please enter a valid weight.")
        
    if math.isnan(weight) or math.isinf(weight):
        raise ValueError("Please enter a valid weight.")
        
    if weight <= 0:
        raise ValueError("Weight must be greater than zero.")

    # Realistic boundary check (soft validation)
    if weight > 700:
        raise ValueError("Weight entered exceeds realistic limits (max 700 kg).")

    # 3. Validate Height
    if height_str is None or not str(height_str).strip():
        raise ValueError("Please enter a valid height.")
        
    clean_h_str = str(height_str).strip().replace(",", ".")
    try:
        height = float(clean_h_str)
    except (ValueError, TypeError):
        raise ValueError("Please enter a valid height.")
        
    if math.isnan(height) or math.isinf(height):
        raise ValueError("Please enter a valid height.")
        
    if height <= 0:
        raise ValueError("Height must be greater than zero.")

    # Realistic boundary check (soft validation)
    if height > 3.0:
        raise ValueError("Height entered exceeds realistic limits (max 3.0 m).")

    return cleaned_name, weight, height
