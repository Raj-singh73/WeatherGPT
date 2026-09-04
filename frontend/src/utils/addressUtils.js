/**
 * addressUtils.js - User Account Address Helper Utilities for WeatherGPT
 */

export const getUserAccountAddress = (user) => {
  if (!user) return null;
  const village = user.village?.trim();
  const district = user.district?.trim();
  const state = user.state?.trim();

  if (village && district) {
    if (village.toLowerCase() === district.toLowerCase()) {
      return district;
    }
    return `${village}, ${district}`;
  }
  if (district) {
    return district;
  }
  if (state) {
    return state;
  }
  return null;
};

