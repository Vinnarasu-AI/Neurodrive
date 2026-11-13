import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import ApplicationCards from '../components/ApplicationCards';

describe('ApplicationCards Component', () => {
  it('renders all three application cards', () => {
    render(
      <ApplicationCards
        currentMode="IDLE"
        onActivateSmartHome={() => {}}
        onActivateGame={() => {}}
        onActivateWheelchair={() => {}}
        onDeactivate={() => {}}
        isCalibrated={false}
        isSignalGood={true}
      />
    );

    expect(screen.getByText('Smart Home Automation')).toBeDefined();
    expect(screen.getByText('EOG Dino Runner Game')).toBeDefined();
    expect(screen.getByText('Assistive Wheelchair')).toBeDefined();
  });

  it('shows Deactivate button when Smart Home is active', () => {
    render(
      <ApplicationCards
        currentMode="SMART_HOME_ACTIVE"
        onActivateSmartHome={() => {}}
        onActivateGame={() => {}}
        onActivateWheelchair={() => {}}
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
        onActivateWheelchair={() => {}}
        onDeactivate={() => {}}
        isCalibrated={true}
        isSignalGood={true}
      />
    );

    expect(screen.getByText('Deactivate Game')).toBeDefined();
  });

  it('shows Deactivate button when Wheelchair is active', () => {
    render(
      <ApplicationCards
        currentMode="WHEELCHAIR_ACTIVE"
        onActivateSmartHome={() => {}}
        onActivateGame={() => {}}
        onActivateWheelchair={() => {}}
        onDeactivate={() => {}}
        isCalibrated={true}
        isSignalGood={true}
      />
    );

    expect(screen.getByText('Deactivate Wheelchair')).toBeDefined();
  });
});
