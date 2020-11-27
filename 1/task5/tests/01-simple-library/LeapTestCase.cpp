//
// Created by akhtyamovpavel on 5/1/20.
//

#include "LeapTestCase.h"

#include <Functions.h>


TEST(TestLeap, NotPositive) {
  ASSERT_THROW(IsLeap(0), std::invalid_argument);
}

TEST(TestLeap, NotDevidedByFour) {
  EXPECT_FALSE(IsLeap(1));
  EXPECT_FALSE(IsLeap(2));
  EXPECT_FALSE(IsLeap(3));
}

TEST(TestLeap, DevidedByFourNotDevidedByHundred) {
  EXPECT_TRUE(IsLeap(4));
  EXPECT_TRUE(IsLeap(8));
  EXPECT_TRUE(IsLeap(12));
}

TEST(TestLeap, DevidedByHundredNotDevidedByFourHudreds) {
  EXPECT_FALSE(IsLeap(100));
  EXPECT_FALSE(IsLeap(200));
  EXPECT_FALSE(IsLeap(300));
}

TEST(TestLeap, DevidedByFourHundreds) {
  EXPECT_TRUE(IsLeap(400));
  EXPECT_TRUE(IsLeap(800));
  EXPECT_TRUE(IsLeap(1200));
}
