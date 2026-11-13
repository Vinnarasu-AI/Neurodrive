import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import ApplicationCards from '../components/ApplicationCards';

describe('ApplicationCards Component', () => {
  it('renders all four application cards', () => {
    render(
      <ApplicationCards
        currentMode="IDLE"
        onActivateSmartHome={() => {}}
        onActivateGame={() => {}}
        onActivateRover={() => {}}
        onDeactivate={() => {}}
        isCalibrated={false}
        isSignalGood={true}
      />
    );

    expect(screen.getByText('Smart Home Automation')).toBeDefined();
    expect(screen.getByText('EOG Dino Runner Game')).toBeDefined();
    expect(screen.getByText('MOVO Delivery Rover')).toBeDefined();
    expect(screen.getByText('Wheelchair Control')).toBeDefined();
  });

  it('ensures Wheelchair card is strictly Coming Soon and disabled', () => {
    render(
      <ApplicationCards
        currentMode="IDLE"
        onActivateSmartHome={() => {}}
        onActivateGame={() => {}}
        onActivateRover={() => {}}
        onDeactivate={() => {}}
        isCalibrated={false}
        isSignalGood={true}
      />
    );

    const comingSoonBadges = screen.getAllByText('Coming Soon');
    expect(comingSoonBadges.length).toBe(1);

    const lockedButtons = screen.getAllByRole('button', { name: /Locked/i });
    expect(lockedButtons.length).toBe(1);
    expect(lockedButtons[0].hasAttribute('disabled')).toBe(true);
  });

  it('shows Deactivate button when Smart Home is active', () => {
    render(
      <ApplicationCards
        currentMode="SMART_HOME_ACTIVE"
        onActivateSmartHome={() => {}}
        onActivateGame={() => {}}
        onActivateRover={() => {}}
        onDeactivate={() => {}}
        isCalibrated={true}
        isSignalGood={true}
      />
    );

    expect(screen.getByText('Deactivate Smart Home')).toBeDefined();
  });

  it('shows Deactivate button when Game is active', () => {
    render(
      <ApplicationCards
        currentMode="GAME_ACTIVE"
        onActivateSmartHome={() => {}}
        onActivateGame={() => {}}
        onActivateRover={() => {}}
        onDeactivate={() => {}}
        isCalibrated={true}
        isSignalGood={true}
      />
    );

    expect(screen.getByText('Deactivate Game')).toBeDefined();
  });

  it('shows Deactivate button when Rover is active', () => {
    render(
      <ApplicationCards
        currentMode="ROVER_ACTIVE"
        onActivateSmartHome={() => {}}
        onActivateGame={() => {}}
        onActivateRover={() => {}}
        onDeactivate={() => {}}
        isCalibrated={true}
        isSignalGood={true}
      />
    );

    expect(screen.getByText('Deactivate Rover')).toBeDefined();
  });
});
