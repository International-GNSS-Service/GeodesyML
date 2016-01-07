#!/usr/bin/env stack
-- stack --install-ghc runghc --package turtle

{-# LANGUAGE LambdaCase #-}
{-# LANGUAGE OverloadedStrings #-}

import Data.Text (lines)
import Turtle

import Prelude hiding (FilePath, lines)

validate :: [Text] -> IO ExitCode
validate = fmap anyFailure . mapM validateOne
  where
    validateOne xml = shell (xsdv <> " " <> xsd <> " " <> xml) empty
    xsdv = "./xsd-validator/xsdv.sh"
    xsd  = "../schema/GeodesyML.xsd"

-- | Arguments: one or more xml files to validate, or none to validate all
--   xml files in the current directory
main :: IO ()
main = getXML >>= validate >>= \case
         ExitSuccess   -> putStrLn "OK, all documents validated succefully."
         ExitFailure _ -> putStrLn "Error, some documents failed to validate!"
  where
    getXML = do
      args <- arguments
      if null args
        then lines . snd <$> shellStrict "ls *.xml" empty
        else return args

anyFailure :: [ExitCode] -> ExitCode
anyFailure exitCodes =
    case (mconcat $ map AnyFailure exitCodes) of
      AnyFailure c -> c

newtype AnyFailure = AnyFailure ExitCode

instance Monoid AnyFailure where
    mempty = AnyFailure ExitSuccess
    AnyFailure ExitSuccess `mappend` AnyFailure ExitSuccess = AnyFailure  ExitSuccess
    _ `mappend` _                                           = AnyFailure (ExitFailure 1)

