import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'timeFormat',
  standalone: true
})
export class TimeFormatPipe implements PipeTransform {
  transform(value: any): string {
    // If the value is a number (either single/double or multi-digit)
    if (typeof value === 'number') {
      return this.formatTime(value); // Convert to HH:00
    }

    // Handle string input with time duration like "1 day", "2 hours"
    if (typeof value === 'string') {
      // Check for "X day", "X hours", and "X minutes"
      const daysMatch = value.match(/(\d+)\s*day/);
      const hoursMatch = value.match(/(\d+)\s*hour/);
      const minutesMatch = value.match(/(\d+)\s*minute/);
      const timeMatch = value.match(/(\d{1,2}):(\d{2})(?::(\d{2}))?/); // HH:mm or HH:mm:ss format

      let totalMinutes = 0;

      // If days are present, convert days to minutes (1 day = 1440 minutes)
      if (daysMatch) {
        totalMinutes += parseInt(daysMatch[1]) * 24 * 60; // 1 day = 1440 minutes
      }

      // If hours are present, convert hours to minutes
      if (hoursMatch) {
        totalMinutes += parseInt(hoursMatch[1]) * 60;
      }

      // If minutes are present, add them
      if (minutesMatch) {
        totalMinutes += parseInt(minutesMatch[1]);
      }

      // If the value is in "HH:mm" or "HH:mm:ss" format
      if (timeMatch) {
        const hours = parseInt(timeMatch[1], 10);
        const minutes = parseInt(timeMatch[2], 10);
        const seconds = timeMatch[3] ? parseInt(timeMatch[3], 10) : 0;

        // Convert total time to minutes (including seconds)
        totalMinutes += hours * 60 + minutes + Math.floor(seconds / 60); // add seconds converted to minutes
      }

      // Convert total minutes to HH:mm format
      return this.formatTime(totalMinutes);
    }

    // Return value as is if it's not recognized (e.g., null or invalid format)
    return value;
  }

  // Helper method to format minutes into HH:mm
  private formatTime(value: number): string {
    // Convert total minutes to hours and minutes
    const hours = Math.floor(value / 60);
    const minutes = value % 60;

    // Format hours and minutes into HH:mm
    return `${this.pad(hours)}:${this.pad(minutes)}`;
  }

  // Helper method to format time string into HH:mm
  private formatTimeString(hours: string, minutes: string): string {
    const hoursNum = parseInt(hours, 10);
    const minutesNum = parseInt(minutes, 10);
    const formattedHours = this.pad(hoursNum);
    const formattedMinutes = this.pad(minutesNum);
    return `${formattedHours}:${formattedMinutes}`;
  }

  // Helper method to pad single digits with a leading zero
  private pad(num: number): string {
    return num < 10 ? '0' + num : num.toString();
  }
}
