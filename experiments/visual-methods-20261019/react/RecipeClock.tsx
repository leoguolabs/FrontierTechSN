import React, { createContext, useContext } from 'react'

// Recipe time is independent of Remotion's root-composition clamp. In particular,
// the last 24 fps shot must still reach virtual source frame 178.75 at 30 fps.
const RecipeClock = createContext(0)
export const RecipeFrameProvider = ({
  frame,
  children,
}: {
  frame: number
  children: React.ReactNode
}) => <RecipeClock.Provider value={frame}>{children}</RecipeClock.Provider>
export const useRecipeFrame = () => useContext(RecipeClock)
