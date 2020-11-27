//
// Created by akhtyamovpavel on 5/1/20.
//

#include "AddTestCase.h"
#include "Functions.h"

TEST(TestAdd, TwoPlusTwo) {
  EXPECT_EQ(4, Add(2, 2));
}