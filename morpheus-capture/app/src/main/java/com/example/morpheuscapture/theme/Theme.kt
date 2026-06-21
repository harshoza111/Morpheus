package com.example.morpheuscapture.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val MorpheusColorScheme = darkColorScheme(
    primary = PrimaryNeon,
    onPrimary = Color.Black,
    secondary = SecondaryNeon,
    onSecondary = Color.Black,
    tertiary = AccentPink,
    background = DarkBg,
    onBackground = LightText,
    surface = DarkSurface,
    onSurface = LightText,
    surfaceVariant = BorderColor,
    onSurfaceVariant = GrayText,
    error = ErrorRed,
    onError = Color.Black
)

@Composable
fun MorpheusCaptureTheme(
    darkTheme: Boolean = true, // Force dark theme always for Morpheus styling
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = MorpheusColorScheme,
        typography = Typography,
        content = content
    )
}
